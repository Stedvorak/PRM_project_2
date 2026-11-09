# Physical ESP32 webpage check

The final M01 monitoring firmware serves David's PROGMEM page at
http://192.168.4.1/ on Wi-Fi PRM-Project-2 (password prm-lab-2026).
Both the actual page and APIs were tested, without modifying frontend or model.

Evidence:
- H09_browser_board: actual Edge rendering, four probabilities,100real X/Y/Z
  samples,10successful status and9signal responses, no JavaScript exceptions.
- D02_state_update: while the operator moved/rotated the sensor, raw axes changed
  significantly and timestamps advanced. Actual API and browser reported shaking.
  One transient stale display occurred under concurrent clients and recovered;
  no persistent frozen-data condition was reproduced.
- D03_stationary_recheck: after the operator confirmed the sensor stationary on
  the table, all6status responses reported unattached with probabilities
  calm0,fast0,unattached1,shaking0. Signal and status timestamps advanced.
  Served HTML matched the verified web_page.h source after newline normalization.

Example real moving X/Y/Z samples in g:
(-0.57995605,0.35791016,-0.69213867),
(0.41430664,1.04260254,-0.06396484),
(0.74926758,0.45336914,-0.73657227).
On the table, Z was approximately0.94g, X about-0.098g, Y near0; this is an
uncalibrated stationary gravity reading, not a hardcoded1g value. No calibration,
resampling or fabricated signal was introduced during the check.

The frontend plots actual ax_g/ay_g/az_g, not a synthetic gravity line or a
class-derived signal. Near1g on one stationary axis is expected. The classifier
uses a100sample/~4second window, so a stable new state needs a few seconds after
motion stops. No classifier changes or reflash were needed for this check.

For demonstration, open the exact board URL above and refresh with Ctrl+F5 if
an old page is suspected. Check the latest sample timestamp and individual axes.
GitHub Pages /web-station/ is a separate BLE client and requires Connect; it does
not receive board data merely by loading the page. The exact URL of David's
reported persistent display issue was not supplied, so no cache fault is claimed.
