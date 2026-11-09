#pragma once
#include "prm_features.h"
namespace prm {
// M06 v1: grouped evaluation in sibling metrics.json.
inline bool modelAvailable() { return true; }
inline bool predictProbabilities(const float* features, float* probabilities) {
  if (!features || !probabilities) return false;
  for (size_t i=0; i<kFeatureCount; ++i) if (!std::isfinite(features[i])) return false;
  for (size_t i=0; i<kClassCount; ++i) probabilities[i]=0.0f;
  if (features[8] <= 53.336799621582031) {
    if (features[6] <= 0.96633413434028625) {
      if (features[9] <= 0.35086268186569214) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        if (features[9] <= 1.2099857926368713) {
          probabilities[0] += static_cast<float>(0.088483146067415724);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.036516853932584269);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.089285714285714288);
          probabilities[2] += static_cast<float>(0.035714285714285712);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    } else {
      probabilities[0] += static_cast<float>(0.0);
      probabilities[1] += static_cast<float>(0.125);
      probabilities[2] += static_cast<float>(0.0);
      probabilities[3] += static_cast<float>(0.0);
    }
  } else {
    probabilities[0] += static_cast<float>(0.0);
    probabilities[1] += static_cast<float>(0.0);
    probabilities[2] += static_cast<float>(0.0);
    probabilities[3] += static_cast<float>(0.125);
  }
  if (features[7] <= 0.1092868410050869) {
    if (features[8] <= 3.998826265335083) {
      if (features[10] <= 0.0034870852250605822) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        if (features[8] <= 3.3315801620483398) {
          probabilities[0] += static_cast<float>(0.048611111111111112);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.076388888888888895);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.11550632911392406);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.0094936708860759497);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    } else {
      if (features[10] <= 0.024775644764304161) {
        if (features[11] <= 0.030694183893501759) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.041666666666666664);
          probabilities[2] += static_cast<float>(0.083333333333333329);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.125);
          probabilities[2] += static_cast<float>(0.0);
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
  if (features[7] <= 0.1125793531537056) {
    if (features[9] <= 1.2419895529747009) {
      if (features[8] <= 3.276459813117981) {
        if (features[8] <= 3.197358250617981) {
          probabilities[0] += static_cast<float>(0.012500000000000001);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.1125);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.125);
          probabilities[3] += static_cast<float>(0.0);
        }
      } else {
        if (features[7] <= 0.0058666602708399296) {
          probabilities[0] += static_cast<float>(0.1203125);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.0046874999999999998);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.125);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    } else {
      if (features[6] <= 0.96565699577331543) {
        if (features[6] <= 0.94754210114479065) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.125);
          probabilities[2] += static_cast<float>(0.0);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.125);
          probabilities[3] += static_cast<float>(0.0);
        }
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
  if (features[6] <= 1.0015946328639984) {
    if (features[10] <= 0.012695891316980124) {
      if (features[8] <= 3.2827925682067871) {
        if (features[8] <= 3.2535123825073242) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.125);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.027777777777777776);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.097222222222222224);
          probabilities[3] += static_cast<float>(0.0);
        }
      } else {
        if (features[7] <= 0.0057490293402224779) {
          probabilities[0] += static_cast<float>(0.11923076923076924);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.0057692307692307696);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.050000000000000003);
          probabilities[2] += static_cast<float>(0.074999999999999997);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    } else {
      if (features[7] <= 0.0056618864182382822) {
        probabilities[0] += static_cast<float>(0.125);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        if (features[11] <= 0.51515194028615952) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.11029411764705882);
          probabilities[2] += static_cast<float>(0.014705882352941176);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.10416666666666667);
          probabilities[3] += static_cast<float>(0.020833333333333332);
        }
      }
    }
  } else {
    probabilities[0] += static_cast<float>(0.0);
    probabilities[1] += static_cast<float>(0.0);
    probabilities[2] += static_cast<float>(0.0);
    probabilities[3] += static_cast<float>(0.125);
  }
  if (features[11] <= 0.37635242193937302) {
    if (features[8] <= 3.9820102453231812) {
      if (features[7] <= 0.0016924655647017062) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        if (features[9] <= 0.76566341519355774) {
          probabilities[0] += static_cast<float>(0.125);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.0);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.044354838709677422);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.080645161290322578);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    } else {
      if (features[11] <= 0.11537618935108185) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.125);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        if (features[8] <= 10.432989120483398) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.125);
          probabilities[2] += static_cast<float>(0.0);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.125);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    }
  } else {
    if (features[6] <= 0.97775080800056458) {
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
  if (features[7] <= 0.10974942147731781) {
    if (features[8] <= 3.998826265335083) {
      if (features[7] <= 0.0016540659125894308) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        if (features[10] <= 0.010747260414063931) {
          probabilities[0] += static_cast<float>(0.125);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.0);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.02734375);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.09765625);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    } else {
      if (features[8] <= 10.432989120483398) {
        if (features[9] <= 2.6200439929962158) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.12276785714285714);
          probabilities[2] += static_cast<float>(0.002232142857142857);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.098684210526315791);
          probabilities[2] += static_cast<float>(0.026315789473684209);
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
  if (features[9] <= 25.043634414672852) {
    if (features[7] <= 0.0055854632519185543) {
      if (features[11] <= 0.0099009624682366848) {
        if (features[6] <= 0.95508456230163574) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.125);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0625);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.0625);
          probabilities[3] += static_cast<float>(0.0);
        }
      } else {
        if (features[7] <= 0.0019422465120442212) {
          probabilities[0] += static_cast<float>(0.083333333333333329);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.041666666666666664);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.125);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.0);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    } else {
      if (features[6] <= 0.96501258015632629) {
        if (features[6] <= 0.94960832595825195) {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.125);
          probabilities[2] += static_cast<float>(0.0);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.125);
          probabilities[3] += static_cast<float>(0.0);
        }
      } else {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.125);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0);
      }
    }
  } else {
    if (features[6] <= 0.97718781232833862) {
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
  if (features[6] <= 0.99002352356910706) {
    if (features[10] <= 0.012845688499510288) {
      if (features[11] <= 0.00826624920591712) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.125);
        probabilities[3] += static_cast<float>(0.0);
      } else {
        if (features[11] <= 0.029703987762331963) {
          probabilities[0] += static_cast<float>(0.12166666666666667);
          probabilities[1] += static_cast<float>(0.0);
          probabilities[2] += static_cast<float>(0.0033333333333333335);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.021739130434782608);
          probabilities[2] += static_cast<float>(0.10326086956521739);
          probabilities[3] += static_cast<float>(0.0);
        }
      }
    } else {
      if (features[10] <= 0.032630804926156998) {
        if (features[11] <= 0.041807625442743301) {
          probabilities[0] += static_cast<float>(0.020833333333333332);
          probabilities[1] += static_cast<float>(0.041666666666666664);
          probabilities[2] += static_cast<float>(0.0625);
          probabilities[3] += static_cast<float>(0.0);
        } else {
          probabilities[0] += static_cast<float>(0.0);
          probabilities[1] += static_cast<float>(0.11925287356321838);
          probabilities[2] += static_cast<float>(0.0057471264367816091);
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
    if (features[6] <= 1.0087765455245972) {
      if (features[6] <= 1.0010119676589966) {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.125);
      } else {
        probabilities[0] += static_cast<float>(0.0);
        probabilities[1] += static_cast<float>(0.0625);
        probabilities[2] += static_cast<float>(0.0);
        probabilities[3] += static_cast<float>(0.0625);
      }
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
