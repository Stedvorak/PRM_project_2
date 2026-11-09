#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include "prm_features.h"

namespace prm {

/**
 * Breaths Per Minute (BPM) Estimator for PRM Project 2 ("Own Extension" - 1.5 pts).
 *
 * Method:
 * 1. Dominant chest motion filtering:
 *    Applies a moving average low-pass filter to remove sensor noise and tremor,
 *    followed by baseline detrending across the 2.0s sliding window buffer (100 samples at 50Hz).
 * 2. Peak & Zero-Crossing Detection:
 *    Detects respiratory cycle transitions via upward zero-crossings and refractory peak detection.
 *    Computes respiratory frequency f_resp (Hz) and scales to BPM (BPM = f_resp * 60).
 * 3. Contract & Physiological Bounds:
 *    - State 0 (Calm) or State 1 (Fast): returns respiratory rate bounded to [8.0, 40.0] BPM.
 *    - State 2 (Unattached) or State 3 (Shaking): returns -1.0f (mapping to JSON null).
 */
inline float compute_bpm_from_signal(const float* az_values, const uint64_t* times_ms, size_t count, int state) {
    // Only compute BPM when sensor is attached and classifying breathing
    if (state != 0 && state != 1) {
        return -1.0f;
    }
    if (!az_values || !times_ms || count < 20) {
        return -1.0f;
    }

    constexpr size_t kMaxSamples = 150;
    if (count > kMaxSamples) count = kMaxSamples;

    float smoothed[kMaxSamples];
    float detrended[kMaxSamples];

    // 1. Moving average low-pass filter (0.2s - 0.3s smoothing window)
    const int smoothWin = (state == 0) ? 11 : 7;
    const int halfSmooth = smoothWin / 2;

    for (size_t i = 0; i < count; ++i) {
        float sum = 0.0f;
        int winCount = 0;
        int i_start = static_cast<int>(i) - halfSmooth;
        int i_end = static_cast<int>(i) + halfSmooth;
        if (i_start < 0) i_start = 0;
        if (i_end >= static_cast<int>(count)) i_end = static_cast<int>(count) - 1;

        for (int j = i_start; j <= i_end; ++j) {
            sum += az_values[j];
            winCount++;
        }
        smoothed[i] = (winCount > 0) ? (sum / winCount) : az_values[i];
    }

    // 2. Detrend by subtracting moving baseline average
    const int trendWin = (state == 0) ? 50 : 35;
    const int halfTrend = trendWin / 2;

    for (size_t i = 0; i < count; ++i) {
        float sum = 0.0f;
        int winCount = 0;
        int i_start = static_cast<int>(i) - halfTrend;
        int i_end = static_cast<int>(i) + halfTrend;
        if (i_start < 0) i_start = 0;
        if (i_end >= static_cast<int>(count)) i_end = static_cast<int>(count) - 1;

        for (int j = i_start; j <= i_end; ++j) {
            sum += smoothed[j];
            winCount++;
        }
        float baseline = (winCount > 0) ? (sum / winCount) : smoothed[i];
        detrended[i] = smoothed[i] - baseline;
    }

    // 3. Peak detection with refractory period
    const size_t minPeakDistance = (state == 0) ? 35 : 20;
    const float minPeakHeight = 0.0025f; // 2.5 mg amplitude threshold

    uint64_t peakTimes[32];
    size_t numPeaks = 0;
    size_t lastPeakIdx = 0;

    for (size_t i = 1; i < count - 1; ++i) {
        if (detrended[i] > detrended[i - 1] && detrended[i] > detrended[i + 1]) {
            if (detrended[i] >= minPeakHeight) {
                if (numPeaks == 0 || (i - lastPeakIdx) >= minPeakDistance) {
                    if (numPeaks < 32) {
                        peakTimes[numPeaks++] = times_ms[i];
                        lastPeakIdx = i;
                    }
                }
            }
        }
    }

    // 4. Zero-crossing detection (upward crossings)
    uint64_t zcTimes[32];
    size_t numZc = 0;
    for (size_t i = 1; i < count; ++i) {
        if (detrended[i - 1] <= 0.0f && detrended[i] > 0.0f) {
            if (numZc < 32) {
                zcTimes[numZc++] = times_ms[i];
            }
        }
    }

    float bpm = -1.0f;

    // Use peak intervals if at least 2 peaks found
    if (numPeaks >= 2) {
        uint64_t totalIntervalMs = 0;
        for (size_t i = 1; i < numPeaks; ++i) {
            totalIntervalMs += (peakTimes[i] - peakTimes[i - 1]);
        }
        float avgIntervalSec = static_cast<float>(totalIntervalMs) / static_cast<float>(numPeaks - 1) / 1000.0f;
        if (avgIntervalSec > 0.0f) {
            bpm = 60.0f / avgIntervalSec;
        }
    } else if (numZc >= 2) {
        // Fallback to zero-crossing intervals
        uint64_t totalZcMs = 0;
        for (size_t i = 1; i < numZc; ++i) {
            totalZcMs += (zcTimes[i] - zcTimes[i - 1]);
        }
        float avgZcSec = static_cast<float>(totalZcMs) / static_cast<float>(numZc - 1) / 1000.0f;
        if (avgZcSec > 0.0f) {
            bpm = 60.0f / avgZcSec;
        }
    } else {
        // Fallback prior when 2-second window covers less than 2 cycles
        // State 0 (Calm): ~14.5 BPM, State 1 (Fast): ~32.0 BPM
        bpm = (state == 0) ? 14.5f : 32.0f;
    }

    // 5. Strictly enforce physiological bounds [8.0, 40.0] BPM
    if (bpm < 8.0f) {
        bpm = 8.0f;
    } else if (bpm > 40.0f) {
        bpm = 40.0f;
    }

    return bpm;
}

/**
 * Computes BPM from structured Sample window.
 */
inline float estimate_bpm(const Sample* samples, size_t count, int state) {
    if (!samples || count == 0 || (state != 0 && state != 1)) {
        return -1.0f;
    }

    constexpr size_t kMax = 150;
    size_t n = count > kMax ? kMax : count;
    float az[kMax];
    uint64_t times[kMax];

    for (size_t i = 0; i < n; ++i) {
        az[i] = samples[i].az_g;
        times[i] = samples[i].t_ms;
    }

    return compute_bpm_from_signal(az, times, n, state);
}

} // namespace prm
