#pragma once

#include <cstdint>

#ifndef PRM_INFERENCE_DIAGNOSTICS
#define PRM_INFERENCE_DIAGNOSTICS 0
#endif

#if PRM_INFERENCE_DIAGNOSTICS
#include <Arduino.h>
#endif

namespace prm {

// Testing-only USB telemetry. The default demonstration build emits nothing.
// Timing values must come from actual on-board measurements by the caller.
inline void emitInferenceDiagnostic(
    uint64_t timestamp_ms, uint8_t state, const float* probabilities,
    uint32_t feature_us, uint32_t predict_us, uint32_t total_us,
    uint64_t window_first_ms, uint64_t window_last_ms, uint64_t sample_gap_ms) {
#if PRM_INFERENCE_DIAGNOSTICS
  if (!probabilities) return;
  Serial.printf(
      "# INFERENCE {\"t_ms\":%llu,\"state_id\":%u,"
      "\"feature_us\":%lu,\"predict_us\":%lu,\"total_us\":%lu,"
      "\"probabilities\":[%.9f,%.9f,%.9f,%.9f],"
      "\"window_first_ms\":%llu,\"window_last_ms\":%llu,"
      "\"sample_gap_ms\":%llu}\n",
      static_cast<unsigned long long>(timestamp_ms), static_cast<unsigned>(state),
      static_cast<unsigned long>(feature_us), static_cast<unsigned long>(predict_us),
      static_cast<unsigned long>(total_us), probabilities[0], probabilities[1],
      probabilities[2], probabilities[3], static_cast<unsigned long long>(window_first_ms),
      static_cast<unsigned long long>(window_last_ms),
      static_cast<unsigned long long>(sample_gap_ms));
#else
  (void)timestamp_ms; (void)state; (void)probabilities; (void)feature_us;
  (void)predict_us; (void)total_us; (void)window_first_ms;
  (void)window_last_ms; (void)sample_gap_ms;
#endif
}

}  // namespace prm
