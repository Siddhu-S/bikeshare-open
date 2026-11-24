# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

- Added cnt_roll_28, which is the mean of count over the 28 days before d. It is valid since it is available at prediction time because every input is dated before d. To do this I had to raise LAG_WARMUP to 28 and change cnt_lag_7 and cnt_roll_7 to a hard coded 7 so they did not also become 28-day features.
- It beat validation too so I kept cnt_roll_28. The validation R^2 rose from 0.6462 to 0.6839 for ridge and from 0.1929 to 0.2415 for hgb which exceeds the noise threshold.
