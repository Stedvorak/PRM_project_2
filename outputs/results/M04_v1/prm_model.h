#pragma once
#include "prm_features.h"
namespace prm {
// M04 v1: grouped evaluation in sibling metrics.json.
inline bool modelAvailable() { return true; }
inline bool predictProbabilities(const float* features, float* probabilities) {
  if (!features || !probabilities) return false;
  for (size_t i=0; i<kFeatureCount; ++i) if (!std::isfinite(features[i])) return false;
  double logits[4] = {};
  logits[0] = 2.2151768451613325 + (1.6230471436468747) * static_cast<double>(features[0]) + (3.7405417484564882) * static_cast<double>(features[1]) + (3.9444070914283458) * static_cast<double>(features[2]) + (-0.67256267472308928) * static_cast<double>(features[3]) + (-4.2759682153129912) * static_cast<double>(features[4]) + (-3.9139193927042153) * static_cast<double>(features[5]) + (-4.0196287852421486) * static_cast<double>(features[6]) + (-3.8693914089810089) * static_cast<double>(features[7]) + (-0.0067792223381985973) * static_cast<double>(features[8]) + (-0.026742873762412744) * static_cast<double>(features[9]) + (-0.89453184419811393) * static_cast<double>(features[10]) + (-1.2920067307644088) * static_cast<double>(features[11]);
  logits[1] = -0.40598328445945198 + (-18.414390235067927) * static_cast<double>(features[0]) + (2.5791881489727668) * static_cast<double>(features[1]) + (-11.999727482184376) * static_cast<double>(features[2]) + (-0.21758378567616993) * static_cast<double>(features[3]) + (3.1037876056097513) * static_cast<double>(features[4]) + (3.1285437495268393) * static_cast<double>(features[5]) + (2.7056603782201751) * static_cast<double>(features[6]) + (2.7635485426840343) * static_cast<double>(features[7]) + (0.0043406628217830907) * static_cast<double>(features[8]) + (0.019674894031694118) * static_cast<double>(features[9]) + (0.53508029196811746) * static_cast<double>(features[10]) + (0.93433852073877222) * static_cast<double>(features[11]);
  logits[2] = 4.6670174715841695 + (8.1175659989288622) * static_cast<double>(features[0]) + (-5.7261856044558606) * static_cast<double>(features[1]) + (6.8490615878434014) * static_cast<double>(features[2]) + (-0.3520723065302927) * static_cast<double>(features[3]) + (-2.8240774942766853) * static_cast<double>(features[4]) + (-0.72810624101529964) * static_cast<double>(features[5]) + (-2.8796054397741306) * static_cast<double>(features[6]) + (-1.7996758577682468) * static_cast<double>(features[7]) + (-0.0086241787632823988) * static_cast<double>(features[8]) + (-0.013461781785238165) * static_cast<double>(features[9]) + (-1.1246810927156898) * static_cast<double>(features[10]) + (-0.27872353884980833) * static_cast<double>(features[11]);
  logits[3] = -6.4762110322860558 + (8.6737770924921911) * static_cast<double>(features[0]) + (-0.59354429297339617) * static_cast<double>(features[1]) + (1.2062588029126278) * static_cast<double>(features[2]) + (1.2422187669295666) * static_cast<double>(features[3]) + (3.9962581039799376) * static_cast<double>(features[4]) + (1.5134818841926887) * static_cast<double>(features[5]) + (4.193573846796081) * static_cast<double>(features[6]) + (2.9055187240652343) * static_cast<double>(features[7]) + (0.011062738279697925) * static_cast<double>(features[8]) + (0.020529761515956889) * static_cast<double>(features[9]) + (1.4841326449456913) * static_cast<double>(features[10]) + (0.63639174887545491) * static_cast<double>(features[11]);
  double largest=logits[0];
  for (size_t i=1; i<4; ++i) if(logits[i]>largest) largest=logits[i];
  double total=0.0;
  for (size_t i=0; i<4; ++i) { logits[i]=std::exp(logits[i]-largest); total+=logits[i]; }
  if (!std::isfinite(total) || total<=0.0) return false;
  for (size_t i=0; i<4; ++i) probabilities[i]=static_cast<float>(logits[i]/total);
  return true;
}
}  // namespace prm
