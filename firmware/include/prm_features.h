#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>

namespace prm {

constexpr size_t kWindowSamples = 100;
constexpr size_t kFeatureCount = 10;
constexpr size_t kClassCount = 4;

struct Sample {
  uint64_t t_ms;
  float ax_g, ay_g, az_g;
  float gx_dps, gy_dps, gz_dps;
};

/**
 * Extracts 10 robust, low-complexity features from 100 six-axis samples:
 * f[0]: acc_mag_std       (std of acceleration magnitude)
 * f[1]: acc_mag_range     (range of acceleration magnitude)
 * f[2]: gyro_mag_std      (std of gyro magnitude)
 * f[3]: gyro_mag_range    (range of gyro magnitude)
 * f[4]: var_ax            (variance of ax)
 * f[5]: var_ay            (variance of ay)
 * f[6]: var_az            (variance of az)
 * f[7]: mean_ax           (mean of ax)
 * f[8]: mean_az           (mean of az)
 * f[9]: log_var_acc_mag   (log of variance of acceleration magnitude)
 */
inline bool extractFeatures(const Sample* samples, size_t count, float* out) {
  if (!samples || !out || count != kWindowSamples) return false;

  double sum_ax = 0.0, sq_ax = 0.0;
  double sum_ay = 0.0, sq_ay = 0.0;
  double sum_az = 0.0, sq_az = 0.0;
  double sum_amag = 0.0, sq_amag = 0.0;
  double sum_gmag = 0.0, sq_gmag = 0.0;

  double min_amag = 1.0e30, max_amag = -1.0e30;
  double min_gmag = 1.0e30, max_gmag = -1.0e30;

  for (size_t i = 0; i < count; ++i) {
    const Sample& s = samples[i];
    if (!std::isfinite(s.ax_g) || !std::isfinite(s.ay_g) || !std::isfinite(s.az_g) ||
        !std::isfinite(s.gx_dps) || !std::isfinite(s.gy_dps) || !std::isfinite(s.gz_dps)) {
      return false;
    }
    if (i && (s.t_ms <= samples[i - 1].t_ms || s.t_ms - samples[i - 1].t_ms > 80)) {
      return false;
    }

    const double ax = s.ax_g;
    const double ay = s.ay_g;
    const double az = s.az_g;
    const double gx = s.gx_dps;
    const double gy = s.gy_dps;
    const double gz = s.gz_dps;

    const double amag = std::sqrt(ax * ax + ay * ay + az * az);
    const double gmag = std::sqrt(gx * gx + gy * gy + gz * gz);

    sum_ax += ax; sq_ax += ax * ax;
    sum_ay += ay; sq_ay += ay * ay;
    sum_az += az; sq_az += az * az;

    sum_amag += amag; sq_amag += amag * amag;
    sum_gmag += gmag; sq_gmag += gmag * gmag;

    if (amag < min_amag) min_amag = amag;
    if (amag > max_amag) max_amag = amag;
    if (gmag < min_gmag) min_gmag = gmag;
    if (gmag > max_gmag) max_gmag = gmag;
  }

  const double invN = 1.0 / count;

  const double mean_ax = sum_ax * invN;
  const double mean_ay = sum_ay * invN;
  const double mean_az = sum_az * invN;
  const double mean_amag = sum_amag * invN;
  const double mean_gmag = sum_gmag * invN;

  const double var_ax = (sq_ax * invN) - (mean_ax * mean_ax);
  const double var_ay = (sq_ay * invN) - (mean_ay * mean_ay);
  const double var_az = (sq_az * invN) - (mean_az * mean_az);

  const double var_amag = (sq_amag * invN) - (mean_amag * mean_amag);
  const double var_gmag = (sq_gmag * invN) - (mean_gmag * mean_gmag);

  const double std_amag = std::sqrt(var_amag > 0.0 ? var_amag : 0.0);
  const double std_gmag = std::sqrt(var_gmag > 0.0 ? var_gmag : 0.0);

  const double amag_range = max_amag - min_amag;
  const double gmag_range = max_gmag - min_gmag;

  const double log_var_amag = std::log((var_amag > 0.0 ? var_amag : 0.0) + 1.0e-6);

  out[0] = static_cast<float>(std_amag);
  out[1] = static_cast<float>(amag_range);
  out[2] = static_cast<float>(std_gmag);
  out[3] = static_cast<float>(gmag_range);
  out[4] = static_cast<float>(var_ax > 0.0 ? var_ax : 0.0);
  out[5] = static_cast<float>(var_ay > 0.0 ? var_ay : 0.0);
  out[6] = static_cast<float>(var_az > 0.0 ? var_az : 0.0);
  out[7] = static_cast<float>(mean_ax);
  out[8] = static_cast<float>(mean_az);
  out[9] = static_cast<float>(log_var_amag);

  for (size_t i = 0; i < kFeatureCount; ++i) {
    if (!std::isfinite(out[i])) return false;
  }
  return true;
}

}  // namespace prm
