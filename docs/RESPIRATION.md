# M07 v1: experimental breathing-rate extension

The existing dashboard renders numeric breaths_per_min, but the earlier firmware
always returned null. M07 computes an estimate from genuine acceleration on the
ESP32; it does not change or retrain the selected M01 v1 classifier or BLE.
Implementation: firmware/include/prm_respiration.h and firmware/src/main.cpp.

Five consecutive 25 Hz readings are averaged per point; 100 points provide
approximately 20 seconds of history. The estimator removes linear drift and
gravity/DC from each axis, selects the axis with greatest remaining variance,
and finds a normalized autocorrelation peak. Actual timestamps determine the
rate. Comparable shorter peaks avoid selecting doubled periods. Guards require
at least three periods, 9-45 breaths/min, correlation >=0.65 and detrended RMS
0.0015-0.15 g. These are experimental engineering thresholds, not calibration.

Gross motion (acceleration magnitude outside 0.5-1.5 g or angular speed above
80 deg/s), gaps, nonfinite input and sensor failure reset history. Only a current
calm/fast prediction allows a numeric HTTP rate. Unattached/shaking clears the
history. Missing/unreliable estimates remain null, displayed as N/A; no default
rate or class-derived value is supplied. HTTP/BLE schemas are unchanged.

## Demonstration

Use a separate phone/laptop on PRM-Project-2, password prm-lab-2026, and open
http://192.168.4.1/. Keep the main PC on eduroam as requested. Press the sensor
against the chest with stable placement and breathe naturally for at least
20 seconds while M01 shows calm/fast. The estimate refreshes once per second.
Count breaths independently over a timed interval before assessing accuracy.
After changing pace, allow the 20-second history to refill. Removing the sensor
should clear the estimate. Repeated M01 state changes can prevent warmup.

## Evidence boundaries

The C++ synthetic test source tests known periods, noise and reset behavior;
it is not recorded data. Expanded validation was stopped at the user's request;
do not claim unexecuted tests passed. Run tests/test_respiration.py with a host
compiler configured in PRM_HOST_CXX to execute it. Existing recordings lack
independently counted respiratory-rate ground truth, so no physiological accuracy
is claimed. Periodic nonbreathing motion, harmonic ambiguity and placement changes
remain limitations. Physical counted-breath verification is outstanding.
