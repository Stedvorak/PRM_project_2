#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>

namespace prm {

constexpr size_t kWindowSamples = 100;
constexpr size_t kFeatureCount = 12;
constexpr size_t kClassCount = 4;

struct Sample {
  uint64_t t_ms;
  float ax_g, ay_g, az_g;
  float gx_dps, gy_dps, gz_dps;
};

// M01 v1: identical order and population variance to tools/train_model.py.
// All samples must be real, finite and strictly time ordered. No interpolation.
inline bool extractFeatures(const Sample* samples, size_t count, float* out) {
  if (!samples || !out || count != kWindowSamples) return false;
  double sums[5] = {};
  double squares[5] = {};
  double deltaSquares = 0.0;
  double magMin = 1.0e30, magMax = -1.0e30;
  for (size_t i = 0; i < count; ++i) {
    const Sample& s = samples[i];
    const double channels[6] = {s.ax_g, s.ay_g, s.az_g,
                                s.gx_dps, s.gy_dps, s.gz_dps};
    for (size_t j = 0; j < 6; ++j) {
      if (!std::isfinite(channels[j])) return false;
    }
    if (i && (s.t_ms <= samples[i - 1].t_ms ||
              s.t_ms - samples[i - 1].t_ms > 80)) return false;
    const double acceleration = std::sqrt(channels[0] * channels[0] +
        channels[1] * channels[1] + channels[2] * channels[2]);
    const double gyro = std::sqrt(channels[3] * channels[3] +
        channels[4] * channels[4] + channels[5] * channels[5]);
    const double values[5] = {channels[0], channels[1], channels[2],
                               acceleration, gyro};
    for (size_t j = 0; j < 5; ++j) {
      sums[j] += values[j];
      squares[j] += values[j] * values[j];
    }
    if (acceleration < magMin) magMin = acceleration;
    if (acceleration > magMax) magMax = acceleration;
    if (i) {
      const double dx = channels[0] - samples[i - 1].ax_g;
      const double dy = channels[1] - samples[i - 1].ay_g;
      const double dz = channels[2] - samples[i - 1].az_g;
      deltaSquares += dx * dx + dy * dy + dz * dz;
    }
  }
  double means[5], deviations[5];
  for (size_t j = 0; j < 5; ++j) {
    means[j] = sums[j] / count;
    double variance = squares[j] / count - means[j] * means[j];
    deviations[j] = std::sqrt(variance > 0.0 ? variance : 0.0);
  }
  const double features[kFeatureCount] = {
      means[0], means[1], means[2], deviations[0], deviations[1], deviations[2],
      means[3], deviations[3], means[4], deviations[4],
      std::sqrt(deltaSquares / (count - 1)), magMax - magMin};
  for (size_t i = 0; i < kFeatureCount; ++i) {
    out[i] = static_cast<float>(features[i]);
    if (!std::isfinite(out[i])) return false;
  }
  return true;
}

}  // namespace prm
