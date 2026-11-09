#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include "prm_features.h"

namespace prm {

/**
 * Dedicated 5.0-second (250 samples @ 50 Hz) Respiratory Rate Estimator.
 *
 * Maintains a continuous circular buffer across successive inference windows
 * to ensure that slow calm breathing cycles (T_resp = 3.0 to 5.0 s / 12-20 BPM)
 * are fully captured and accurately evaluated.
 */
class RespiratoryEstimator {
 public:
  static constexpr size_t kCapacity = 250; // 5.0s at 50Hz (or 10.0s at 25Hz)

  void reset() {
    count_ = 0;
    head_ = 0;
    lastPushedTimeMs_ = 0;
    lastValidBpm_ = -1.0f;
    validBpmTimestampMs_ = 0;
  }

  void pushSample(float az_g, uint64_t t_ms) {
    if (!std::isfinite(az_g)) return;
    // Detect timestamp rewind or long acquisition gap
    if (count_ > 0 && (t_ms < lastPushedTimeMs_ || (t_ms - lastPushedTimeMs_) > 5000)) {
      count_ = 0;
      head_ = 0;
    }
    if (count_ > 0 && t_ms <= lastPushedTimeMs_) return;

    azBuffer_[head_] = az_g;
    timeBuffer_[head_] = t_ms;
    head_ = (head_ + 1) % kCapacity;
    if (count_ < kCapacity) ++count_;
    lastPushedTimeMs_ = t_ms;
  }

  void pushWindow(const Sample* samples, size_t count) {
    if (!samples || count == 0) return;
    // Detect timestamp rewind or long acquisition gap
    if (count_ > 0 && (samples[0].t_ms < lastPushedTimeMs_ || (samples[0].t_ms - lastPushedTimeMs_) > 5000)) {
      reset();
    }
    for (size_t i = 0; i < count; ++i) {
      if (count_ == 0 || samples[i].t_ms > lastPushedTimeMs_) {
        pushSample(samples[i].az_g, samples[i].t_ms);
      }
    }
  }

  size_t count() const { return count_; }
  float lastValidBpm() const { return lastValidBpm_; }

  float computeBpm(int state) {
    // Return null / -1.0f immediately for unattached or shaking states
    if (state != 0 && state != 1) {
      lastValidBpm_ = -1.0f;
      return -1.0f;
    }

    // Need at least 40 samples (~0.8s - 1.6s) to begin estimation
    if (count_ < 40) {
      return (lastValidBpm_ > 0.0f) ? lastValidBpm_ : -1.0f;
    }

    // Linearize circular buffer into chronological array
    float az[kCapacity];
    uint64_t times[kCapacity];
    const size_t start = (count_ == kCapacity) ? head_ : 0;
    for (size_t i = 0; i < count_; ++i) {
      const size_t idx = (start + i) % kCapacity;
      az[i] = azBuffer_[idx];
      times[i] = timeBuffer_[idx];
    }

    // 1. Moving average smoothing filter (approx 0.3s window: 15 samples @ 50Hz)
    const int smoothWin = (state == 0) ? 17 : 11;
    const int halfSmooth = smoothWin / 2;
    float smoothed[kCapacity];

    for (size_t i = 0; i < count_; ++i) {
      float sum = 0.0f;
      int winCount = 0;
      int i_start = static_cast<int>(i) - halfSmooth;
      int i_end = static_cast<int>(i) + halfSmooth;
      if (i_start < 0) i_start = 0;
      if (i_end >= static_cast<int>(count_)) i_end = static_cast<int>(count_) - 1;
      for (int j = i_start; j <= i_end; ++j) {
        sum += az[j];
        winCount++;
      }
      smoothed[i] = (winCount > 0) ? (sum / winCount) : az[i];
    }

    // 2. Detrend by subtracting moving baseline average (approx 2.0s - 3.0s window)
    const int trendWin = (state == 0) ? 85 : 45;
    const int halfTrend = trendWin / 2;
    float detrended[kCapacity];
    float minVal = 1e9f, maxVal = -1e9f;

    for (size_t i = 0; i < count_; ++i) {
      float sum = 0.0f;
      int winCount = 0;
      int i_start = static_cast<int>(i) - halfTrend;
      int i_end = static_cast<int>(i) + halfTrend;
      if (i_start < 0) i_start = 0;
      if (i_end >= static_cast<int>(count_)) i_end = static_cast<int>(count_) - 1;
      for (int j = i_start; j <= i_end; ++j) {
        sum += smoothed[j];
        winCount++;
      }
      float baseline = (winCount > 0) ? (sum / winCount) : smoothed[i];
      detrended[i] = smoothed[i] - baseline;
      if (detrended[i] < minVal) minVal = detrended[i];
      if (detrended[i] > maxVal) maxVal = detrended[i];
    }

    // Breathing amplitude threshold check (at least 0.0025g / 2.5mg amplitude)
    const float ampPtp = maxVal - minVal;
    if (ampPtp < 0.0025f) {
      // If breathing stops or amplitude is below threshold, hold last valid estimate or decay gracefully
      if (lastValidBpm_ > 0.0f) {
        uint64_t now = times[count_ - 1];
        if (now > validBpmTimestampMs_ && (now - validBpmTimestampMs_) > 8000) {
          lastValidBpm_ = -1.0f; // decay to null after 8 seconds of no breathing motion
        }
        return lastValidBpm_;
      }
      return -1.0f;
    }

    // Calculate actual sample duration dtSec
    float dtSec = 0.02f;
    if (count_ > 1) {
      dtSec = static_cast<float>(times[count_ - 1] - times[0]) / static_cast<float>(count_ - 1) / 1000.0f;
      if (dtSec <= 0.0f || dtSec > 0.1f) dtSec = 0.02f;
    }

    // 3. Find prominent peaks with minimum refractory distance (at least 0.8s apart)
    const size_t minPeakDistance = static_cast<size_t>(std::round(0.8f / dtSec));
    const float peakThreshold = 0.0018f;

    uint64_t peakTimes[32];
    size_t numPeaks = 0;
    size_t lastPeakIdx = 0;

    for (size_t i = 1; i < count_ - 1; ++i) {
      if (detrended[i] > detrended[i - 1] && detrended[i] > detrended[i + 1]) {
        if (detrended[i] >= peakThreshold) {
          if (numPeaks == 0 || (i - lastPeakIdx) >= minPeakDistance) {
            if (numPeaks < 32) {
              peakTimes[numPeaks++] = times[i];
              lastPeakIdx = i;
            }
          }
        }
      }
    }

    float bpm = -1.0f;

    // Calculate instantaneous BPM from the average interval of the last 2 peak-to-peak cycles
    if (numPeaks >= 2) {
      size_t startCycle = (numPeaks >= 3) ? (numPeaks - 3) : (numPeaks - 2);
      float totalIntervalSec = 0.0f;
      size_t intervalCount = 0;
      for (size_t i = startCycle + 1; i < numPeaks; ++i) {
        float intSec = static_cast<float>(peakTimes[i] - peakTimes[i - 1]) / 1000.0f;
        if (intSec >= 1.2f && intSec <= 7.5f) { // 8 to 50 BPM cycle duration
          totalIntervalSec += intSec;
          intervalCount++;
        }
      }
      if (intervalCount > 0) {
        float avgTcycle = totalIntervalSec / static_cast<float>(intervalCount);
        bpm = 60.0f / avgTcycle;
      }
    }

    // Troughs detection as secondary or zero crossings
    if (bpm < 8.0f || bpm > 40.0f) {
      uint64_t troughTimes[32];
      size_t numTroughs = 0;
      size_t lastTroughIdx = 0;
      for (size_t i = 1; i < count_ - 1; ++i) {
        if (detrended[i] < detrended[i - 1] && detrended[i] < detrended[i + 1]) {
          if (detrended[i] <= -peakThreshold) {
            if (numTroughs == 0 || (i - lastTroughIdx) >= minPeakDistance) {
              if (numTroughs < 32) {
                troughTimes[numTroughs++] = times[i];
                lastTroughIdx = i;
              }
            }
          }
        }
      }
      if (numTroughs >= 2) {
        size_t startCycle = (numTroughs >= 3) ? (numTroughs - 3) : (numTroughs - 2);
        float totalIntSec = 0.0f;
        size_t intCount = 0;
        for (size_t i = startCycle + 1; i < numTroughs; ++i) {
          float intSec = static_cast<float>(troughTimes[i] - troughTimes[i - 1]) / 1000.0f;
          if (intSec >= 1.2f && intSec <= 7.5f) {
            totalIntSec += intSec;
            intCount++;
          }
        }
        if (intCount > 0) {
          bpm = 60.0f / (totalIntSec / static_cast<float>(intCount));
        }
      }
    }

    // Zero-crossing fallback over the 5-second buffer
    if (bpm < 8.0f || bpm > 40.0f) {
      const size_t minZcDist = static_cast<size_t>(std::round(0.5f / dtSec));
      float zcTimes[32];
      size_t numZc = 0;
      size_t lastZcIdx = 0;
      for (size_t i = 1; i < count_; ++i) {
        if ((detrended[i - 1] <= 0.0f && detrended[i] > 0.0f) ||
            (detrended[i - 1] >= 0.0f && detrended[i] < 0.0f)) {
          if (numZc == 0 || (i - lastZcIdx) >= minZcDist) {
            if (numZc < 32) {
              float dy = detrended[i] - detrended[i - 1];
              float frac = (std::fabs(dy) > 1e-6f) ? (-detrended[i - 1] / dy) : 0.5f;
              if (frac < 0.0f) frac = 0.0f;
              if (frac > 1.0f) frac = 1.0f;
              float t_zc = static_cast<float>(times[i - 1]) + frac * static_cast<float>(times[i] - times[i - 1]);
              zcTimes[numZc++] = t_zc;
              lastZcIdx = i;
            }
          }
        }
      }
      if (numZc >= 2) {
        size_t startZc = (numZc >= 3) ? (numZc - 3) : (numZc - 2);
        float totalHalfSec = 0.0f;
        size_t halfCount = 0;
        for (size_t i = startZc + 1; i < numZc; ++i) {
          float halfSec = (zcTimes[i] - zcTimes[i - 1]) / 1000.0f;
          if (halfSec >= 0.6f && halfSec <= 3.75f) {
            totalHalfSec += halfSec;
            halfCount++;
          }
        }
        if (halfCount > 0) {
          float avgHalf = totalHalfSec / static_cast<float>(halfCount);
          bpm = 30.0f / avgHalf;
        }
      }
    }

    // Physiological bounds: [8.0, 40.0] BPM
    if (bpm >= 8.0f && bpm <= 40.0f) {
      lastValidBpm_ = bpm;
      validBpmTimestampMs_ = times[count_ - 1];
      return bpm;
    }

    // Hold last valid estimate if available
    if (lastValidBpm_ > 0.0f) {
      return lastValidBpm_;
    }

    return -1.0f;
  }

 private:
  float azBuffer_[kCapacity]{};
  uint64_t timeBuffer_[kCapacity]{};
  size_t count_ = 0;
  size_t head_ = 0;
  uint64_t lastPushedTimeMs_ = 0;
  float lastValidBpm_ = -1.0f;
  uint64_t validBpmTimestampMs_ = 0;
};

inline RespiratoryEstimator& get_respiratory_estimator() {
  static RespiratoryEstimator s_estimator;
  return s_estimator;
}

/**
 * Computes BPM from structured Sample window.
 * Feeds samples continuously into the dedicated 250-sample (5.0s) circular buffer.
 */
inline float estimate_bpm(const Sample* samples, size_t count, int state) {
  if (state != 0 && state != 1) {
    get_respiratory_estimator().reset();
    return -1.0f;
  }

  auto& estimator = get_respiratory_estimator();
  estimator.pushWindow(samples, count);
  return estimator.computeBpm(state);
}

/**
 * Standalone evaluator for array buffers (used in verification tests).
 */
inline float compute_bpm_from_signal(const float* az_values, const uint64_t* times_ms, size_t count, int state) {
  if (state != 0 && state != 1) {
    return -1.0f;
  }
  if (!az_values || !times_ms || count < 20) {
    return -1.0f;
  }

  RespiratoryEstimator standalone;
  for (size_t i = 0; i < count; ++i) {
    standalone.pushSample(az_values[i], times_ms[i]);
  }
  return standalone.computeBpm(state);
}

} // namespace prm
