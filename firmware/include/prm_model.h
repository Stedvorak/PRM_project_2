#pragma once

#include "prm_features.h"

namespace prm {

// No real recordings have been trained/evaluated yet. Never substitute
// synthetic weights or a hand-written class for a missing trained model.
inline bool modelAvailable() { return false; }
inline bool predictProbabilities(const float*, float*) { return false; }

}  // namespace prm
