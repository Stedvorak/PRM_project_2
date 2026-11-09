#pragma once
#include "prm_features.h"

namespace prm {
// M05 v1: trained from real_sensor manifest; see metrics.json.
inline bool modelAvailable() { return true; }
inline bool predictProbabilities(const float* features, float* probabilities) {
  if (!features || !probabilities) return false;
  for (size_t i = 0; i < kFeatureCount; ++i)
    if (!std::isfinite(features[i])) return false;
  if (features[8] <= 53.336799621582031) {
    if (features[9] <= 1.2419895529747009) {
      if (features[8] <= 3.2498193979263306) {
        if (features[6] <= 0.95516115427017212) {
          probabilities[0] = static_cast<float>(0.0);
          probabilities[1] = static_cast<float>(0.0);
          probabilities[2] = static_cast<float>(1.0);
          probabilities[3] = static_cast<float>(0.0);
        } else {
          probabilities[0] = static_cast<float>(0.5);
          probabilities[1] = static_cast<float>(0.0);
          probabilities[2] = static_cast<float>(0.5);
          probabilities[3] = static_cast<float>(0.0);
        }
      } else {
        if (features[11] <= 0.031996911391615868) {
          if (features[7] <= 0.0016540659125894308) {
            probabilities[0] = static_cast<float>(0.0);
            probabilities[1] = static_cast<float>(0.0);
            probabilities[2] = static_cast<float>(1.0);
            probabilities[3] = static_cast<float>(0.0);
          } else {
            probabilities[0] = static_cast<float>(1.0);
            probabilities[1] = static_cast<float>(0.0);
            probabilities[2] = static_cast<float>(0.0);
            probabilities[3] = static_cast<float>(0.0);
          }
        } else {
          probabilities[0] = static_cast<float>(0.0);
          probabilities[1] = static_cast<float>(0.0);
          probabilities[2] = static_cast<float>(1.0);
          probabilities[3] = static_cast<float>(0.0);
        }
      }
    } else {
      if (features[9] <= 14.222309589385986) {
        if (features[7] <= 0.0057893751654773951) {
          probabilities[0] = static_cast<float>(0.0);
          probabilities[1] = static_cast<float>(0.5);
          probabilities[2] = static_cast<float>(0.5);
          probabilities[3] = static_cast<float>(0.0);
        } else {
          if (features[10] <= 0.024775644764304161) {
            probabilities[0] = static_cast<float>(0.0);
            probabilities[1] = static_cast<float>(1.0);
            probabilities[2] = static_cast<float>(0.0);
            probabilities[3] = static_cast<float>(0.0);
          } else {
            probabilities[0] = static_cast<float>(0.0);
            probabilities[1] = static_cast<float>(0.66666666666666663);
            probabilities[2] = static_cast<float>(0.33333333333333331);
            probabilities[3] = static_cast<float>(0.0);
          }
        }
      } else {
        probabilities[0] = static_cast<float>(0.0);
        probabilities[1] = static_cast<float>(0.0);
        probabilities[2] = static_cast<float>(1.0);
        probabilities[3] = static_cast<float>(0.0);
      }
    }
  } else {
    probabilities[0] = static_cast<float>(0.0);
    probabilities[1] = static_cast<float>(0.0);
    probabilities[2] = static_cast<float>(0.0);
    probabilities[3] = static_cast<float>(1.0);
  }
  return true;
}

}  // namespace prm
