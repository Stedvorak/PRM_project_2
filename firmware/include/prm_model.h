#pragma once

#include "prm_features.h"
#include "model.h"

namespace prm {

inline bool modelAvailable() {
  return true;
}

inline bool predictProbabilities(const float* features, float* probabilities) {
  if (!features || !probabilities) return false;
  int state = predict_sensor_state(features, probabilities);
  return state >= 0 && state < 4;
}

}  // namespace prm
