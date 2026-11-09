#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include <LittleFS.h>
#include <NimBLEDevice.h>
#include <Adafruit_NeoPixel.h>
#include <esp_timer.h>
#include <freertos/semphr.h>
#include "nimble/porting/nimble/include/nimble/nimble_port.h"

#include "prm_config.h"
#include "prm_features.h"
#include "prm_model.h"
#include "prm_runtime.h"
#include "bpm.h"
#include "web_page.h"

namespace {
uint64_t nowMs() { return static_cast<uint64_t>(esp_timer_get_time()) / 1000; }

struct Prediction {
  bool valid = false;
  uint64_t inferredAt = 0;
  uint8_t state = 0;
  float probabilities[prm::kClassCount]{};
  float confidence = 0.0f;
  float breaths_per_min = -1.0f;
};

prm::SampleRing samples;
Prediction prediction;
portMUX_TYPE stateMux = portMUX_INITIALIZER_UNLOCKED;
bool sensorHealthy = false;
uint8_t activeMpuAddress = 0;  // No address is usable until ACK and identity pass.
uint64_t lastSampleAt = 0;
uint64_t nextSensorAttempt = 0;
uint64_t nextPoll = 0;
uint64_t nextInference = 0;
uint64_t nextBle = 0;
bool filesystemReady = false;
NimBLECharacteristic* stateCharacteristic = nullptr;
NimBLEServer* bleServer = nullptr;
SemaphoreHandle_t bleValueMutex = nullptr;
ble_npl_event blePublishEvent{};
bool blePublishQueued = false;
portMUX_TYPE bleQueueMux = portMUX_INITIALIZER_UNLOCKED;
WebServer http(80);
#if PRM_RGB_PIN >= 0
Adafruit_NeoPixel rgb(1, PRM_RGB_PIN, NEO_GRB + NEO_KHZ800);
#endif

void updateLed(bool ready, uint8_t state) {
#if PRM_RGB_PIN >= 0
  uint32_t color = 0;
  if (ready) {
    switch (state) {
      case 0: color = rgb.Color(0, 24, 0); break;
      case 1: color = rgb.Color(24, 0, 0); break;
      case 2: color = rgb.Color(0, 0, 24); break;
      case 3: color = rgb.Color(24, 0, 24); break;
    }
  }
  // Off means unavailable. It is never mapped to one of the four classes.
  static uint32_t previous = UINT32_MAX;
  if (previous != color) { rgb.setPixelColor(0, color); rgb.show(); previous = color; }
#else
  (void)ready;
  (void)state;
#endif
}

bool readyLocked(uint64_t now) {
  return sensorHealthy && samples.size() == prm::kWindowSamples && prediction.valid &&
         now >= lastSampleAt && now - lastSampleAt <= prm::kSensorStaleMs &&
         now >= prediction.inferredAt && now - prediction.inferredAt <= prm::kPredictionStaleMs;
}

Prediction predictionSnapshot(uint64_t& now, bool& ready) {
  portENTER_CRITICAL(&stateMux);
  now = nowMs();  // Match readiness age checks to this exact locked snapshot.
  Prediction copy = prediction;
  ready = readyLocked(now);
  portEXIT_CRITICAL(&stateMux);
  return copy;
}

// Caller holds bleValueMutex. Do not hold stateMux around a NimBLE call.
void applyReadableState(const Prediction& copy, bool ready) {
  if (ready) {
    uint8_t payload[2];
    payload[0] = copy.state;
    payload[1] = (copy.breaths_per_min > 0.0f) ? static_cast<uint8_t>(std::round(copy.breaths_per_min)) : 0;
    stateCharacteristic->setValue(payload, 2);
  } else {
    const uint8_t empty = 0;
    stateCharacteristic->setValue(&empty, 0);
  }
}

void setReadableState(uint64_t now) {
  if (!stateCharacteristic || !bleValueMutex) return;
  xSemaphoreTake(bleValueMutex, portMAX_DELAY);
  bool ready;
  const Prediction copy = predictionSnapshot(now, ready);
  applyReadableState(copy, ready);
  xSemaphoreGive(bleValueMutex);
}

void queueBlePublication() {
  if (!stateCharacteristic || !bleValueMutex) return;
  bool enqueue = false;
  portENTER_CRITICAL(&bleQueueMux);
  if (!blePublishQueued) { blePublishQueued = true; enqueue = true; }
  portEXIT_CRITICAL(&bleQueueMux);
  if (enqueue) ble_npl_eventq_put(nimble_port_get_dflt_eventq(), &blePublishEvent);
}

// State transitions that could invalidate a published prediction use the same
// mutex. A notification cannot be sent after a concurrently committed failure.
void lockPublicationState() {
  if (bleValueMutex) xSemaphoreTake(bleValueMutex, portMAX_DELAY);
}
void unlockPublicationState() {
  if (bleValueMutex) xSemaphoreGive(bleValueMutex);
}

void invalidateSensor(uint64_t now) {
  lockPublicationState();
  portENTER_CRITICAL(&stateMux);
  sensorHealthy = false;
  prediction.valid = false;
  samples.clear();
  portEXIT_CRITICAL(&stateMux);
  unlockPublicationState();
  activeMpuAddress = 0;
  nextSensorAttempt = now + prm::kSensorRetryMs;
  queueBlePublication();
}

void checkFreshness(uint64_t now) {
  if (sensorHealthy && now >= lastSampleAt && now - lastSampleAt > prm::kSensorStaleMs)
    invalidateSensor(now);
}

bool writeRegister(uint8_t reg, uint8_t value) {
  if (!activeMpuAddress) return false;
  Wire.beginTransmission(activeMpuAddress);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission(true) == 0;
}

bool readRegistersAt(uint8_t address, uint8_t reg, uint8_t* data, size_t count) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  const size_t received = Wire.requestFrom(address, count, true);
  if (received != count) {
    while (Wire.available()) Wire.read();
    return false;
  }
  for (size_t i = 0; i < count; ++i) data[i] = static_cast<uint8_t>(Wire.read());
  return true;
}

bool readRegisters(uint8_t reg, uint8_t* data, size_t count) {
  return activeMpuAddress && readRegistersAt(activeMpuAddress, reg, data, count);
}

bool detectSensor() {
  activeMpuAddress = 0;
  const uint8_t candidates[] = {
      PRM_MPU_ADDRESS, static_cast<uint8_t>(PRM_MPU_ADDRESS ^ 0x01)};
  const size_t candidateCount = PRM_MPU_AUTO_DETECT ? 2 : 1;
  // This is targeted detection, never a generic bus scan. An ACK alone cannot
  // authorize MPU register writes: WHO_AM_I must also identify an MPU-6050.
  for (size_t i = 0; i < candidateCount; ++i) {
    const uint8_t address = candidates[i];
    Wire.beginTransmission(address);
    const bool acknowledged = Wire.endTransmission(true) == 0;
    uint8_t identity = 0;
    const bool identified = acknowledged && readRegistersAt(address, 0x75, &identity, 1);
    if (identified && identity == 0x68) {
      activeMpuAddress = address;
#if PRM_CAPTURE_SERIAL
      Serial.printf("# I2C detection: MPU-6050 verified at 0x%02X\n", address);
#endif
      return true;
    }
  }
#if PRM_CAPTURE_SERIAL
  Serial.println("# I2C detection: no verified MPU-6050; measurements unavailable");
#endif
  return false;
}

bool initializeSensor() {
  // Run before every reset/configuration attempt, including recovery retries.
  if (!detectSensor()) return false;
  if (!writeRegister(0x6B, 0x80)) return false;
  delay(100);  // Reset settling, outside the sampling loop.
  if (!writeRegister(0x6B, 0x01)) return false;
  delay(10);
  // DLPF=5: accel/gyro bandwidth 10Hz, below the 12.5Hz Nyquist limit.
  // Gyro internal output remains 1kHz; sample divider 39 -> 25Hz.
  return writeRegister(0x1A, 0x05) && writeRegister(0x19, 39) &&
         writeRegister(0x1B, 0x00) && writeRegister(0x1C, 0x00) &&
         writeRegister(0x38, 0x01);
}

int16_t signedWord(const uint8_t* bytes) {
  return static_cast<int16_t>((static_cast<uint16_t>(bytes[0]) << 8) | bytes[1]);
}

enum class ReadResult { sample, notReady, failure };
ReadResult readSensor(prm::Sample& sample) {
  uint8_t status;
  if (!readRegisters(0x3A, &status, 1)) return ReadResult::failure;
  if ((status & 0x01) == 0) return ReadResult::notReady;
  uint8_t raw[14];
  if (!readRegisters(0x3B, raw, sizeof(raw))) return ReadResult::failure;
  sample = {nowMs(), signedWord(raw) / 16384.0f, signedWord(raw + 2) / 16384.0f,
            signedWord(raw + 4) / 16384.0f, signedWord(raw + 8) / 131.0f,
            signedWord(raw + 10) / 131.0f, signedWord(raw + 12) / 131.0f};
  return ReadResult::sample;
}

void sampleSensor(uint64_t now) {
  if (!sensorHealthy) {
    if (now < nextSensorAttempt) return;
    if (!initializeSensor()) { nextSensorAttempt = nowMs() + prm::kSensorRetryMs; return; }
    now = nowMs();
    lockPublicationState();
    portENTER_CRITICAL(&stateMux);
    sensorHealthy = true;
    lastSampleAt = now;
    samples.clear();
    prediction.valid = false;
    portEXIT_CRITICAL(&stateMux);
    unlockPublicationState();
    nextPoll = now;
  }
  if (now < nextPoll) return;
  nextPoll = now + prm::kSamplePeriodMs;  // Never manufacture catch-up readings.
  prm::Sample sample;
  const ReadResult result = readSensor(sample);
  if (result == ReadResult::failure) { invalidateSensor(nowMs()); return; }
  if (result == ReadResult::notReady) return;
  bool pushed;
  lockPublicationState();
  portENTER_CRITICAL(&stateMux);
  if (samples.size() && sample.t_ms - lastSampleAt > 80) {
    samples.clear();  // Do not run a fixed-rate model across a long acquisition gap.
    prediction.valid = false;
  }
  pushed = samples.push(sample);
  if (pushed) lastSampleAt = sample.t_ms;
  portEXIT_CRITICAL(&stateMux);
  unlockPublicationState();
  if (!pushed) { invalidateSensor(nowMs()); return; }
#if PRM_CAPTURE_SERIAL
  Serial.printf("%llu,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f\n",
                static_cast<unsigned long long>(sample.t_ms), sample.ax_g, sample.ay_g,
                sample.az_g, sample.gx_dps, sample.gy_dps, sample.gz_dps);
#endif
}

void infer(uint64_t now) {
  if (now < nextInference) return;
  nextInference = now + prm::kInferencePeriodMs;
  if (!prm::modelAvailable()) return;
  prm::Sample window[prm::kWindowSamples];
  size_t count;
  bool healthy;
  portENTER_CRITICAL(&stateMux);
  count = samples.copyTo(window);
  const uint64_t snapshotAt = nowMs();
  healthy = sensorHealthy && snapshotAt >= lastSampleAt &&
            snapshotAt - lastSampleAt <= prm::kSensorStaleMs;
  portEXIT_CRITICAL(&stateMux);
  float features[prm::kFeatureCount];
  Prediction next;
  if (healthy && prm::sampleWindowContinuous(window, count) &&
      prm::extractFeatures(window, count, features) &&
      prm::predictProbabilities(features, next.probabilities) &&
      prm::validateProbabilities(next.probabilities, next.state, next.confidence)) {
    next.valid = true;
    next.inferredAt = nowMs();
    next.breaths_per_min = prm::estimate_bpm(window, count, next.state);
  }
  lockPublicationState();
  portENTER_CRITICAL(&stateMux);
  prediction = next;
  portEXIT_CRITICAL(&stateMux);
  unlockPublicationState();
}

String timestampString(uint64_t value) {
  char text[24];
  snprintf(text, sizeof(text), "%llu", static_cast<unsigned long long>(value));
  return String(text);
}

void sendJson(const String& body) {
  http.sendHeader("Cache-Control", "no-store");
  http.send(200, "application/json", body);
}

void handleStatus() {
  uint64_t now = nowMs();
  bool ready;
  const Prediction copy = predictionSnapshot(now, ready);
  String body;
  body.reserve(400);
  body = "{\"ready\":";
  body += ready ? "true" : "false";
  body += ",\"timestamp_ms\":";
  body += timestampString(now);
  if (!ready) {
    body += ",\"state\":null,\"state_id\":null,\"probabilities\":null,\"confidence\":null,\"breaths_per_min\":null}";
  } else {
    body += ",\"state\":\"";
    body += prm::kStateNames[copy.state];
    body += "\",\"state_id\":";
    body += String(copy.state);
    body += ",\"probabilities\":{";
    for (size_t i = 0; i < prm::kClassCount; ++i) {
      if (i) body += ',';
      body += '"'; body += prm::kStateNames[i]; body += "\":";
      body += String(copy.probabilities[i], 8);
    }
    body += "},\"confidence\":";
    body += String(copy.confidence, 8);
    if (copy.breaths_per_min > 0.0f) {
      body += ",\"breaths_per_min\":";
      body += String(copy.breaths_per_min, 1);
      body += "}";
    } else {
      body += ",\"breaths_per_min\":null}";
    }
  }
  sendJson(body);
}

void handleSignal() {
  prm::Sample window[prm::kWindowSamples];
  portENTER_CRITICAL(&stateMux);
  const uint64_t now = nowMs();
  const size_t count = sensorHealthy && now >= lastSampleAt &&
      now - lastSampleAt <= prm::kSensorStaleMs ? samples.copyTo(window) : 0;
  portEXIT_CRITICAL(&stateMux);
  String body;
  body.reserve(11000);
  body = "{\"sample_rate_hz\":25,\"unit\":\"g\",\"samples\":[";
  for (size_t i = 0; i < count; ++i) {
    if (i) body += ',';
    body += "{\"t_ms\":"; body += timestampString(window[i].t_ms);
    body += ",\"ax_g\":"; body += String(window[i].ax_g, 8);
    body += ",\"ay_g\":"; body += String(window[i].ay_g, 8);
    body += ",\"az_g\":"; body += String(window[i].az_g, 8);
    body += '}';
  }
  body += "]}";
  sendJson(body);
}

String contentType(const String& path) {
  if (path.endsWith(".html")) return "text/html";
  if (path.endsWith(".js")) return "application/javascript";
  if (path.endsWith(".css")) return "text/css";
  if (path.endsWith(".json")) return "application/json";
  if (path.endsWith(".svg")) return "image/svg+xml";
  if (path.endsWith(".png")) return "image/png";
  if (path.endsWith(".ico")) return "image/x-icon";
  return "application/octet-stream";
}

void handleAsset() {
  if (http.method() != HTTP_GET) { http.send(405, "text/plain", "GET required"); return; }
  String path = http.uri();
  if (path.indexOf("..") >= 0 || path.indexOf('\\') >= 0) {
    http.send(400, "text/plain", "Invalid asset path"); return;
  }
  if (path == "/") path = "/index.html";
  if (path == "/index.html") {
    http.sendHeader("Cache-Control", "no-store");
    http.send_P(200, "text/html", INDEX_HTML);
    return;
  }
  if (!filesystemReady || !LittleFS.exists(path)) {
    http.send(path == "/index.html" ? 503 : 404, "text/plain",
              "Frontend asset unavailable. API: /api/status and /api/signal");
    return;
  }
  File file = LittleFS.open(path, "r");
  if (!file || file.isDirectory()) { http.send(404, "text/plain", "Asset not found"); return; }
  http.sendHeader("Cache-Control", "no-store");
  http.streamFile(file, contentType(path));
  file.close();
}

class StateCallbacks : public NimBLECharacteristicCallbacks {
  void onRead(NimBLECharacteristic*) override { setReadableState(nowMs()); }
};
class ServerCallbacks : public NimBLEServerCallbacks {
  void onDisconnect(NimBLEServer*) override { NimBLEDevice::startAdvertising(); }
};

// All runtime characteristic mutations and notifications execute on the NimBLE
// host task, serially with READ and subscription callbacks. This also protects
// NimBLE 1.4.2's subscription vector from cross-task notification iteration.
void publishBleEvent(ble_npl_event*) {
  portENTER_CRITICAL(&bleQueueMux);
  blePublishQueued = false;
  portEXIT_CRITICAL(&bleQueueMux);
  xSemaphoreTake(bleValueMutex, portMAX_DELAY);
  uint64_t now = nowMs();
  bool ready;
  const Prediction copy = predictionSnapshot(now, ready);
  // Exactly one snapshot drives all three outputs; no second readiness capture.
  applyReadableState(copy, ready);
  updateLed(ready, copy.state);
  if (now >= nextBle) {
    nextBle = now + prm::kBlePeriodMs;
    if (ready && bleServer && bleServer->getConnectedCount()) {
      uint8_t payload[2];
      payload[0] = copy.state;
      payload[1] = (copy.breaths_per_min > 0.0f) ? static_cast<uint8_t>(std::round(copy.breaths_per_min)) : 0;
      stateCharacteristic->notify(payload, 2);
    }
  }
  xSemaphoreGive(bleValueMutex);
}

void initializeBle() {
  bleValueMutex = xSemaphoreCreateMutex();
  if (!bleValueMutex) return;
  NimBLEDevice::init(prm::kDeviceName);
  ble_npl_event_init(&blePublishEvent, publishBleEvent, nullptr);
  bleServer = NimBLEDevice::createServer();
  bleServer->setCallbacks(new ServerCallbacks());
  NimBLEService* service = bleServer->createService(prm::kServiceUuid);
  stateCharacteristic = service->createCharacteristic(
      prm::kStateUuid, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY, 2);
  stateCharacteristic->setCallbacks(new StateCallbacks());
  setReadableState(nowMs());
  service->start();
  NimBLEAdvertising* advertising = NimBLEDevice::getAdvertising();
  advertising->addServiceUUID(prm::kServiceUuid);
  advertising->setScanResponse(true);
  advertising->start();
}

void updateBleAndLed(uint64_t now) {
  static uint64_t nextPublication = 0;
  if (now < nextPublication) return;
  nextPublication = now + prm::kSamplePeriodMs;
  queueBlePublication();
}

void acquisitionTask(void*) {
  for (;;) {
    const uint64_t now = nowMs();
    checkFreshness(now);
    sampleSensor(now);
    infer(nowMs());
    updateBleAndLed(nowMs());
    vTaskDelay(pdMS_TO_TICKS(1));
  }
}
}  // namespace

void setup() {
#if PRM_CAPTURE_SERIAL
  Serial.begin(115200);
  Serial.println("t_ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps");
#endif
#if PRM_RGB_PIN >= 0
  rgb.begin();
  updateLed(false, 0);
#endif
  Wire.begin(PRM_I2C_SDA, PRM_I2C_SCL);
  Wire.setClock(400000);
  Wire.setTimeOut(20);
  initializeBle();
  WiFi.mode(WIFI_AP);
  WiFi.softAP(PRM_AP_SSID, PRM_AP_PASSWORD);
  filesystemReady = LittleFS.begin(false);  // Never format or overwrite frontend assets automatically.
  http.on("/api/status", HTTP_GET, handleStatus);
  http.on("/api/signal", HTTP_GET, handleSignal);
  http.onNotFound(handleAsset);
  http.begin();
  // HTTP may wait on a client. Acquisition and BLE cadence must continue anyway.
  const BaseType_t taskStarted = xTaskCreatePinnedToCore(
      acquisitionTask, "prm-acquisition", 12288, nullptr, 1, nullptr, 1);
  if (taskStarted != pdPASS) invalidateSensor(nowMs());
}

void loop() {
  http.handleClient();
  delay(1);
}
