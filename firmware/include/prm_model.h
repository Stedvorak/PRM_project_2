#pragma once
#include "prm_features.h"

namespace prm {
// M01 v1: trained from real_sensor manifest; see metrics.json.
inline bool modelAvailable() { return true; }
inline bool predictProbabilities(const float* features, float* probabilities) {
  if (!features || !probabilities) return false;
  for (size_t i = 0; i < kFeatureCount; ++i)
    if (!std::isfinite(features[i])) return false;
  if (features[1] <= 0.64949890971183777) {
    if (features[8] <= 53.336799621582031) {
      probabilities[0] = static_cast<float>(0.0);
      probabilities[1] = static_cast<float>(0.0);
      probabilities[2] = static_cast<float>(1.0);
      probabilities[3] = static_cast<float>(0.0);
    } else {
      probabilities[0] = static_cast<float>(0.0);
      probabilities[1] = static_cast<float>(0.0);
      probabilities[2] = static_cast<float>(0.0);
      probabilities[3] = static_cast<float>(1.0);
    }
  } else {
    if (features[9] <= 1.2419895529747009) {
      probabilities[0] = static_cast<float>(1.0);
      probabilities[1] = static_cast<float>(0.0);
      probabilities[2] = static_cast<float>(0.0);
      probabilities[3] = static_cast<float>(0.0);
    } else {
      probabilities[0] = static_cast<float>(0.0);
      probabilities[1] = static_cast<float>(1.0);
      probabilities[2] = static_cast<float>(0.0);
      probabilities[3] = static_cast<float>(0.0);
    }
  }
  return true;
}

}  // namespace prm
