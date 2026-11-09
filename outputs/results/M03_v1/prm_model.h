#pragma once
#include "prm_features.h"
namespace prm {
// M03 v1: grouped evaluation in sibling metrics.json.
inline bool modelAvailable() { return true; }
inline bool predictProbabilities(const float* features, float* probabilities) {
  if (!features || !probabilities) return false;
  for (size_t i=0; i<kFeatureCount; ++i) if (!std::isfinite(features[i])) return false;
  for (size_t i=0; i<kClassCount; ++i) probabilities[i]=0.0f;
  if (features[8] <= 53.336799621582031) {
    if (features[9] <= 1.2099857926368713) {
      if (features[2] <= 0.69987913966178894) {
        probabilities[0] += static_cast<float>(0.125);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      }
    } else {
      if (features[10] <= 0.024419032037258148) {
        if (features[0] <= 0.002268676646053791) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.125);
          probabilities[2] += static_cast<float>(0.0);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0625);
          probabilities[2] += static_cast<float>(0.0625);
          probabilities[3] += static_cast<float>(0.0);
        }
      } else {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      }
    }
  } else {
    probabilities[0] += static_cast<float>(0.0);
    probabilities[1] += static_cast<float>(0.0);
    probabilities[2] += static_cast<float>(0.0);
    probabilities[3] += static_cast<float>(0.125);
  }
  if (features[2] <= 0.55123990774154663) {
    if (features[8] <= 3.998826265335083) {
      probabilities[0] += static_cast<float>(0.125);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.0);
    } else {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.125);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.0);
    }
  } else {
    if (features[10] <= 0.26181896775960922) {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.125);
      probabilities[3] += static_cast<float>(0.0);
    } else {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.125);
    }
  }
  if (features[2] <= 0.55123990774154663) {
    if (features[8] <= 4.0129714012145996) {
      probabilities[0] += static_cast<float>(0.125);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.0);
    } else {
      if (features[4] <= 0.025562651455402374) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.125);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0625);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0625);
      }
    }
  } else {
    if (features[7] <= 0.1125793531537056) {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.125);
      probabilities[3] += static_cast<float>(0.0);
    } else {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.125);
    }
  }
  if (features[2] <= 0.54995635151863098) {
    if (features[7] <= 0.0056618864182382822) {
      probabilities[0] += static_cast<float>(0.125);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.0);
    } else {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.125);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.0);
    }
  } else {
    if (features[6] <= 0.97642925381660461) {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.125);
      probabilities[3] += static_cast<float>(0.0);
    } else {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.125);
    }
  }
  if (features[1] <= 0.60995300114154816) {
    if (features[8] <= 54.558073043823242) {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.125);
      probabilities[3] += static_cast<float>(0.0);
    } else {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.125);
    }
  } else {
    if (features[7] <= 0.0055854632519185543) {
      probabilities[0] += static_cast<float>(0.125);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.0);
    } else {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.125);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.0);
    }
  }
  if (features[7] <= 0.10974942147731781) {
    if (features[5] <= 0.01334591768682003) {
      if (features[11] <= 0.0097104678861796856) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        if (features[8] <= 3.2859518527984619) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.125);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.10294117647058823);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.022058823529411766);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    } else {
      if (features[1] <= 0.56317688524723053) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        if (features[11] <= 0.029703987762331963) {
          probabilities[0] += static_cast<float>(0.125);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.0);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.125);
          probabilities[2] += static_cast<float>(0.0);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    }
  } else {
    probabilities[0] += static_cast<float>(0.0);
    probabilities[1] += static_cast<float>(0.0);
    probabilities[2] += static_cast<float>(0.0);
    probabilities[3] += static_cast<float>(0.125);
  }
  if (features[7] <= 0.1125793531537056) {
    if (features[1] <= 0.57171386480331421) {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.125);
      probabilities[3] += static_cast<float>(0.0);
    } else {
      if (features[8] <= 3.9659366607666016) {
        probabilities[0] += static_cast<float>(0.125);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.125);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0);
      }
    }
  } else {
    probabilities[0] += static_cast<float>(0.0);
    probabilities[1] += static_cast<float>(0.0);
    probabilities[2] += static_cast<float>(0.0);
    probabilities[3] += static_cast<float>(0.125);
  }
  if (features[3] <= 0.17903904616832733) {
    if (features[9] <= 1.2253628969192505) {
      if (features[2] <= 0.6998150646686554) {
        probabilities[0] += static_cast<float>(0.125);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      }
    } else {
      if (features[3] <= 0.08623059093952179) {
        if (features[4] <= 0.0061699114739894867) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.041666666666666664);
          probabilities[2] += static_cast<float>(0.083333333333333329);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.12361111111111112);
          probabilities[2] += static_cast<float>(0.0013888888888888889);
          probabilities[3] += static_cast<float>(0.0);
        }
      } else {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      }
    }
  } else {
    if (features[6] <= 0.99339666962623596) {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.041666666666666664);
      probabilities[3] += static_cast<float>(0.083333333333333329);
    } else {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.0);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.125);
    }
  }
  return true;
}
}  // namespace prm
