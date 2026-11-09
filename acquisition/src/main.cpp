#include <Arduino.h>
#include <Wire.h>
#include <esp_timer.h>

#ifndef PRM_I2C_SDA
#define PRM_I2C_SDA 8
#endif
#ifndef PRM_I2C_SCL
#define PRM_I2C_SCL 9
#endif
#ifndef PRM_MPU_ADDRESS
#define PRM_MPU_ADDRESS 0x68
#endif
static_assert(PRM_MPU_ADDRESS == 0x68 || PRM_MPU_ADDRESS == 0x69, "MPU address must be 0x68 or 0x69");

namespace {
constexpr uint64_t kPeriodUs = 20000;
constexpr uint64_t kStaleUs = 200000;
uint8_t activeAddress = 0;
uint64_t nextAttemptUs = 0, nextPollUs = 0, lastSampleUs = 0;
bool healthy = false;

uint64_t nowUs() { return static_cast<uint64_t>(esp_timer_get_time()); }

bool readAt(uint8_t address, uint8_t reg, uint8_t* data, size_t count) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(address, count, true) != count) {
    while (Wire.available()) Wire.read();
    return false;
  }
  for (size_t i = 0; i < count; ++i) data[i] = static_cast<uint8_t>(Wire.read());
  return true;
}

bool writeReg(uint8_t reg, uint8_t value) {
  if (!activeAddress) return false;
  Wire.beginTransmission(activeAddress);
  Wire.write(reg); Wire.write(value);
  return Wire.endTransmission(true) == 0;
}

bool detectAndConfigure() {
  activeAddress = 0;
  const uint8_t candidates[] = {PRM_MPU_ADDRESS, static_cast<uint8_t>(PRM_MPU_ADDRESS ^ 1)};
  for (uint8_t address : candidates) {
    Wire.beginTransmission(address);
    const bool ack = Wire.endTransmission(true) == 0;
    uint8_t identity = 0;
    if (ack && readAt(address, 0x75, &identity, 1) && identity == 0x68) {
      activeAddress = address;
      Serial.printf("# DETECT PASS address=0x%02X who_am_i=0x%02X\n", address, identity);
      break;
    }
    Serial.printf("# DETECT candidate=0x%02X ack=%u who_am_i=0x%02X rejected\n", address, ack, identity);
  }
  if (!activeAddress) {
    Serial.println("# DETECT FAIL no verified MPU-6050; no measurements emitted");
    return false;
  }
  if (!writeReg(0x6B, 0x80)) return false;
  delay(100);
  if (!writeReg(0x6B, 0x01)) return false;
  delay(10);
  // DLPF5: 10Hz anti-alias bandwidth, gyro base 1kHz / (19+1) = 50Hz.
  if (!writeReg(0x1A, 5) || !writeReg(0x19, 19) || !writeReg(0x1B, 0) ||
      !writeReg(0x1C, 0) || !writeReg(0x38, 1)) return false;
  // Verify the actual programmed rate, filter and full-scale registers.
  uint8_t settings[4];
  if (!readAt(activeAddress, 0x19, settings, sizeof(settings)) ||
      settings[0] != 19 || settings[1] != 5 || settings[2] != 0 || settings[3] != 0) {
    Serial.println("# CONFIG FAIL register readback mismatch");
    return false;
  }
  Serial.printf("# CONFIG PASS rate_hz=50 accel_unit=g gyro_unit=deg/s accel_range_g=2 gyro_range_dps=250 dlpf_hz=10 sda=%d scl=%d\n", PRM_I2C_SDA, PRM_I2C_SCL);
  return true;
}

int16_t word(const uint8_t* p) {
  return static_cast<int16_t>((static_cast<uint16_t>(p[0]) << 8) | p[1]);
}

void fault(uint64_t now) {
  Serial.println("# SENSOR FAIL acquisition stopped; retrying detection");
  healthy = false; activeAddress = 0; nextAttemptUs = now + 1000000;
}
}  // namespace

void setup() {
  Serial.begin(115200);
  Wire.begin(PRM_I2C_SDA, PRM_I2C_SCL);
  Wire.setClock(400000); Wire.setTimeOut(20);
  Serial.println("# TRAINING ONLY: USB serial measurements; not demo firmware");
  Serial.println("t_ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps");
}

void loop() {
  uint64_t now = nowUs();
  if (!healthy) {
    if (now < nextAttemptUs) { delay(1); return; }
    if (!detectAndConfigure()) { nextAttemptUs = nowUs() + 1000000; delay(1); return; }
    healthy = true; lastSampleUs = nowUs(); nextPollUs = lastSampleUs;
  }
  now = nowUs();
  if (now - lastSampleUs > kStaleUs) { fault(now); return; }
  // Poll data-ready at 1kHz; sensor itself produces 50Hz measurements. This
  // avoids a second 50Hz software clock drifting past hardware sample edges.
  if (now < nextPollUs) { delay(1); return; }
  nextPollUs = now + 1000;
  uint8_t status = 0;
  if (!readAt(activeAddress, 0x3A, &status, 1)) { fault(nowUs()); return; }
  if (!(status & 1)) { delay(1); return; }
  uint8_t raw[14];
  if (!readAt(activeAddress, 0x3B, raw, sizeof(raw))) { fault(nowUs()); return; }
  const uint64_t sampledAt = nowUs();
  if (sampledAt / 1000 <= lastSampleUs / 1000) return;
  lastSampleUs = sampledAt;
  Serial.printf("%llu,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f\n",
      static_cast<unsigned long long>(sampledAt / 1000),
      word(raw) / 16384.0f, word(raw + 2) / 16384.0f, word(raw + 4) / 16384.0f,
      word(raw + 8) / 131.0f, word(raw + 10) / 131.0f, word(raw + 12) / 131.0f);
  // Only actual data-ready bursts produce rows. No interpolation/catch-up rows.
  delay(1);
}
