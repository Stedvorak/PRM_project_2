#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include "prm_features.h"

namespace prm {

// Hardware-independent storage and checks shared with host verification.
class SampleRing {
 public:
  void clear() { count_ = 0; next_ = 0; }
  size_t size() const { return count_; }
  bool push(const Sample& sample) {
    if (!std::isfinite(sample.ax_g) || !std::isfinite(sample.ay_g) ||
        !std::isfinite(sample.az_g) || !std::isfinite(sample.gx_dps) ||
        !std::isfinite(sample.gy_dps) || !std::isfinite(sample.gz_dps)) return false;
    if (count_ && sample.t_ms <= at(count_ - 1).t_ms) return false;
    data_[next_] = sample;
    next_ = (next_ + 1) % kWindowSamples;
    if (count_ < kWindowSamples) ++count_;
    return true;
  }
  const Sample& at(size_t i) const {
    const size_t start = count_ == kWindowSamples ? next_ : 0;
    return data_[(start + i) % kWindowSamples];
  }
  size_t copyTo(Sample* out) const {
    for (size_t i = 0; i < count_; ++i) out[i] = at(i);
    return count_;
  }
 private:
  Sample data_[kWindowSamples]{};
  size_t count_ = 0;
  size_t next_ = 0;
};

inline bool validateProbabilities(const float* values, uint8_t& state, float& confidence) {
  float sum = 0.0f;
  state = 0;
  confidence = -1.0f;
  for (size_t i = 0; i < kClassCount; ++i) {
    if (!std::isfinite(values[i]) || values[i] < 0.0f || values[i] > 1.0f) return false;
    sum += values[i];
    // Strict > means the lowest state ID wins a tie.
    if (values[i] > confidence) { confidence = values[i]; state = static_cast<uint8_t>(i); }
  }
  return std::fabs(sum - 1.0f) <= 0.001f;
}

inline bool sampleWindowContinuous(const Sample* samples, size_t count) {
  if (count != kWindowSamples) return false;
  for (size_t i = 1; i < count; ++i) {
    if (samples[i].t_ms <= samples[i - 1].t_ms ||
        samples[i].t_ms - samples[i - 1].t_ms > 80) return false;
  }
  return true;
}
}  // namespace prm
