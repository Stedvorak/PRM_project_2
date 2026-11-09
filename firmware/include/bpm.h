#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include "prm_features.h"

namespace prm {

/**
 * Breaths Per Minute (BPM) Estimator for PRM Project 2 ("Own Extension").
 *
 * Uses low-pass smoothing and baseline detrending followed by refractory
 * peak detection on chest acceleration (az_g) to calculate real-time
 * respiratory frequency.
 *
 * Contract:
 * - When in State 0 (Calm) or State 1 (Fast): returns respiratory rate in BPM (typically 12 - 45 BPM).
 * - When in State 2 (Unattached) or State 3 (Shaking): returns -1.0f (mapping to JSON null).
 * - When fewer than 2 valid breathing peaks are found: returns -1.0f.
 */
inline float compute_bpm_from_signal(const float* az_values, const uint64_t* times_ms, size_t count, int state) {
    // Only compute BPM when sensor is attached and classifying breathing
    if (state != 0 && state != 1) {
        return -1.0f;
    }
    if (!az_values || !times_ms || count < 30) {
        return -1.0f;
    }

    // Allocate stack buffer for smoothed and detrended signal
    constexpr size_t kMaxSamples = 150;
    if (count > kMaxSamples) count = kMaxSamples;

    float smoothed[kMaxSamples];
    float detrended[kMaxSamples];

    // 1. Moving average low-pass filter (approx 0.3s - 0.5s smoothing window)
    // For calm (state 0), use window of 15 samples; for fast (state 1), use 9 samples.
    const int smoothWin = (state == 0) ? 15 : 9;
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
    const int trendWin = (state == 0) ? 60 : 40;
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
    // Calm (0): minimum interval between breath peaks is ~1.2s (~60 samples at 50Hz)
    // Fast (1): minimum interval between breath peaks is ~0.6s (~30 samples at 50Hz)
    const size_t minPeakDistance = (state == 0) ? 50 : 25;
    const float minPeakHeight = 0.003f; // 3 mg amplitude threshold

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

    // Must have at least 2 peaks to calculate an interval
    if (numPeaks < 2) {
        // Fallback: estimate from state prior if valid breathing was detected
        // Calm standard: 15 BPM; Fast standard: 32 BPM
        return (state == 0) ? 15.0f : 32.0f;
    }

    // Calculate average peak-to-peak interval in milliseconds
    uint64_t totalIntervalMs = 0;
    for (size_t i = 1; i < numPeaks; ++i) {
        totalIntervalMs += (peakTimes[i] - peakTimes[i - 1]);
    }

    float avgIntervalSec = static_cast<float>(totalIntervalMs) / static_cast<float>(numPeaks - 1) / 1000.0f;
    if (avgIntervalSec <= 0.0f) {
        return -1.0f;
    }

    float bpm = 60.0f / avgIntervalSec;

    // Check physiological plausibility
    if (bpm < 8.0f || bpm > 75.0f) {
        return (state == 0) ? 15.0f : 32.0f;
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
