#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
#include <initializer_list>
#include "prm_respiration.h"

// Mathematical fixtures only; never recorded sensor data or clinical accuracy.
int main() {
  int passed = 0;
  for (const float rate : {12.0f, 18.0f, 30.0f, 40.0f}) {
    for (int axis=0; axis<3; ++axis) {
      prm::RespirationEstimator estimator;
      float bpm = 0;
      for (int i=0; i<800; ++i) {
        const uint64_t t=1000+i*41;  // actual ~24.39 Hz, not assumed 25 Hz
        const float movement=0.015f*std::sin(6.28318530718*rate*t/60000.0);
        prm::Sample s{t,0,0,1,0,0,0};
        if(axis==0) s.ax_g=movement;
        if(axis==1) s.ay_g=movement;
        if(axis==2) s.az_g+=movement;
        estimator.push(s);
        if(i==100) assert(!estimator.estimate(bpm));
      }
      assert(estimator.estimate(bpm));
      assert(std::fabs(bpm-rate)<1.0f);
      ++passed;
    }
  }
  // DC/gravity, linear drift and weak periodic motion must not invent a rate.
  for (int mode=0; mode<4; ++mode) {
    prm::RespirationEstimator estimator;
    unsigned random=42;
    for (int i=0; i<600; ++i) {
      random=1664525u*random+1013904223u;
      const float noise=(static_cast<int>(random>>16)-32768)/32768.0f;
      prm::Sample s{static_cast<uint64_t>(1000+i*40),0,0,1,0,0,0};
      if(mode==1) s.ax_g=i*0.00002f;
      if(mode==2) s.ax_g=0.0001f*std::sin(i*0.1f);
      if(mode==3) s.ax_g=0.01f*noise;
      estimator.push(s);
    }
    float bpm;
    assert(!estimator.estimate(bpm));
    ++passed;
  }
  // Sensor gap, gross motion, nonfinite input and explicit reset invalidate.
  for (int mode=0; mode<4; ++mode) {
    prm::RespirationEstimator estimator;
    for(int i=0;i<500;++i) estimator.push({static_cast<uint64_t>(1000+i*40),
      0.015f*std::sin(i*0.062831853f),0,1,0,0,0});
    float bpm;
    assert(estimator.estimate(bpm));
    prm::Sample s{21000,0,0,1,0,0,0};
    if(mode==0) s.t_ms+=1000;
    if(mode==1) s.gx_dps=100;
    if(mode==2) s.ax_g=std::numeric_limits<float>::quiet_NaN();
    if(mode==3) estimator.clear(); else estimator.push(s);
    assert(!estimator.hasWindow());
    assert(!estimator.estimate(bpm));
    ++passed;
  }
  std::printf("{\"synthetic_cpp_cases_passed\":%d,\"physical_rate_accuracy\":\"not tested\"}\n",passed);
}
