#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include "prm_features.h"

namespace prm {

// M07 v1: experimental periodic chest-motion estimator, independent of M01.
// Five genuine 25 Hz readings are averaged into each point; 100 points give
// about 20 seconds. This is signal processing, not an additional classifier.
class RespirationEstimator {
 public:
  bool hasWindow() const { return count_ == kCount; }
  void clear() {
    count_ = next_ = pending_ = 0;
    lastRaw_ = 0;
    for (float& v : sums_) v = 0;
  }

  void push(const Sample& s) {
    const float v[] = {s.ax_g, s.ay_g, s.az_g, s.gx_dps, s.gy_dps, s.gz_dps};
    for (float x : v) if (!std::isfinite(x)) { clear(); return; }
    if (lastRaw_ && (s.t_ms <= lastRaw_ || s.t_ms - lastRaw_ > 80)) clear();
    lastRaw_ = s.t_ms;
    const float a2 = s.ax_g*s.ax_g + s.ay_g*s.ay_g + s.az_g*s.az_g;
    const float g2 = s.gx_dps*s.gx_dps + s.gy_dps*s.gy_dps + s.gz_dps*s.gz_dps;
    // Gross motion/freefall is not a respiratory measurement.
    if (a2 < 0.25f || a2 > 2.25f || g2 > 6400.0f) { clear(); return; }
    for (size_t k = 0; k < 3; ++k) sums_[k] += v[k];
    if (++pending_ != 5) return;
    Point& p = data_[next_];
    p.t = s.t_ms;
    for (size_t k = 0; k < 3; ++k) { p.a[k] = sums_[k] / 5; sums_[k] = 0; }
    pending_ = 0;
    next_ = (next_ + 1) % kCount;
    if (count_ < kCount) ++count_;
  }

  bool estimate(float& bpm) const {
    bpm = 0;
    if (count_ != kCount) return false;
    const double span = (at(kCount-1).t - at(0).t) / 1000.0;
    if (span < 18.0 || span > 24.0) return false;
    const double step = span / (kCount - 1);
    for (size_t i = 1; i < kCount; ++i) {
      const double dt = (at(i).t - at(i-1).t) / 1000.0;
      if (dt < step * 0.7 || dt > step * 1.3) return false;
    }
    // Remove gravity/DC and a linear drift on each axis. Select the axis with
    // the largest remaining variance, rather than magnitude (which can cancel
    // small chest-induced rotations). The chosen axis is fixed for this window.
    float signal[kCount]{}, candidate[kCount]{};
    double bestEnergy = 0;
    for (size_t axis = 0; axis < 3; ++axis) {
      double sumT=0, sumY=0, sumTT=0, sumTY=0;
      for (size_t i=0; i<kCount; ++i) {
        const double t=(at(i).t-at(0).t)/1000.0, y=at(i).a[axis];
        sumT+=t; sumY+=y; sumTT+=t*t; sumTY+=t*y;
      }
      const double slope=(sumTY-sumT*sumY/kCount)/(sumTT-sumT*sumT/kCount);
      const double offset=(sumY-slope*sumT)/kCount;
      double energy=0;
      for (size_t i=0; i<kCount; ++i) {
        candidate[i]=at(i).a[axis]-offset-slope*(at(i).t-at(0).t)/1000.0;
        energy+=candidate[i]*candidate[i];
      }
      if (energy>bestEnergy) {
        bestEnergy=energy;
        for (size_t i=0; i<kCount; ++i) signal[i]=candidate[i];
      }
    }
    const double rms=std::sqrt(bestEnergy/kCount);
    if (rms<0.0015 || rms>0.15) return false;
    float corr[kCount]{};
    for (size_t lag=1; lag<=kCount/3+1; ++lag) {
      double ab=0, aa=0, bb=0;
      for (size_t i=lag; i<kCount; ++i) {
        ab+=signal[i]*signal[i-lag]; aa+=signal[i]*signal[i]; bb+=signal[i-lag]*signal[i-lag];
      }
      corr[lag]=aa>0 && bb>0 ? ab/std::sqrt(aa*bb) : 0;
    }
    size_t bestLag=0;
    float best=-1;
    // At least three periods, 9-45 breaths/minute. Use actual elapsed time.
    for (size_t lag=2; lag<=kCount/3; ++lag) {
      const double rate=60.0/(lag*step);
      if (rate<9 || rate>45) continue;
      if (corr[lag]>corr[lag-1] && corr[lag]>=corr[lag+1] && corr[lag]>best) {
        best=corr[lag]; bestLag=lag;
      }
    }
    if (!bestLag || best<0.65f) return false;
    // Prefer the fundamental's shortest comparable peak over a doubled period.
    for (size_t lag=2; lag<bestLag; ++lag) {
      const double rate=60.0/(lag*step);
      if (rate>=9 && rate<=45 && corr[lag]>corr[lag-1] && corr[lag]>=corr[lag+1] &&
          corr[lag]>=best-0.05f) { bestLag=lag; break; }
    }
    const double a=corr[bestLag-1], b=corr[bestLag], c=corr[bestLag+1];
    const double denom=a-2*b+c;
    double delta=std::fabs(denom)>1e-9 ? 0.5*(a-c)/denom : 0;
    if (delta < -0.5 || delta > 0.5) delta=0;
    bpm=60.0/((bestLag+delta)*step);
    return std::isfinite(bpm) && bpm>=9 && bpm<=45;
  }

 private:
  static constexpr size_t kCount=100;
  struct Point { uint64_t t=0; float a[3]{}; };
  const Point& at(size_t i) const { return data_[((count_==kCount?next_:0)+i)%kCount]; }
  Point data_[kCount]{};
  size_t count_=0, next_=0, pending_=0;
  uint64_t lastRaw_=0;
  float sums_[3]{};
};
}  // namespace prm
