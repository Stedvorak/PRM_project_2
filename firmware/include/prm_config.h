#pragma once

// These are explicit provisional wiring defaults, not detected hardware facts.
// Override with PlatformIO build_flags after checking the physical board.
#ifndef PRM_I2C_SDA
#define PRM_I2C_SDA 8
#endif
#ifndef PRM_I2C_SCL
#define PRM_I2C_SCL 9
#endif
#ifndef PRM_MPU_ADDRESS
#define PRM_MPU_ADDRESS 0x68
#endif
#ifndef PRM_MPU_AUTO_DETECT
#define PRM_MPU_AUTO_DETECT 1
#endif
static_assert(PRM_MPU_ADDRESS == 0x68 || PRM_MPU_ADDRESS == 0x69,
              "MPU-6050 address must be 0x68 or 0x69");
static_assert(PRM_MPU_AUTO_DETECT == 0 || PRM_MPU_AUTO_DETECT == 1,
              "PRM_MPU_AUTO_DETECT must be 0 or 1");
#ifndef PRM_RGB_PIN
#define PRM_RGB_PIN -1
#endif
#ifndef PRM_CAPTURE_SERIAL
#define PRM_CAPTURE_SERIAL 0
#endif
#ifndef PRM_AP_SSID
#define PRM_AP_SSID "PRM-Project-2"
#endif
#ifndef PRM_AP_PASSWORD
#define PRM_AP_PASSWORD "prm-lab-2026"
#endif

namespace prm {
constexpr const char* kDeviceName = "PRM-Project-2";
constexpr const char* kServiceUuid = "7c2f1000-73ad-4a0d-9ec4-10cc7ea46a10";
constexpr const char* kStateUuid = "7c2f1001-73ad-4a0d-9ec4-10cc7ea46a10";
constexpr unsigned kSamplePeriodMs = 40;
constexpr unsigned kSensorStaleMs = 250;
constexpr unsigned kInferencePeriodMs = 500;
constexpr unsigned kPredictionStaleMs = 1000;
constexpr unsigned kBlePeriodMs = 800;
constexpr unsigned kSensorRetryMs = 1000;
constexpr const char* kStateNames[] = {"calm", "fast", "unattached", "shaking"};
}  // namespace prm
