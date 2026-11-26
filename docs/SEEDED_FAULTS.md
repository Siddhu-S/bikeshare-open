# Seeded faults and failing runs

## Exercise 1: failing test before cnt_roll_28 (written first)

Test: `tests/test_leakage.py::test_cnt_roll_28_matches_hand_computed`.
Expected value is the mean of raw `cnt` for 2011-05-18..2011-06-14, computed from `load_raw()` without any feature helper.

```
F                                                                        [100%]
=================================== FAILURES ===================================
____________________ test_cnt_roll_28_matches_hand_computed ____________________

    def test_cnt_roll_28_matches_hand_computed():
        """cnt_roll_28 on 2011-06-15 must equal mean of cnt for 2011-05-18 through 2011-06-14."""
        feats_df = load_raw()

        # Compute expected value manually from raw data
        target_date = pd.Timestamp("2011-06-15")
        start_date = target_date - pd.Timedelta(days=28)  # 2011-05-18
        end_date = target_date - pd.Timedelta(days=1)     # 2011-06-14

        expected_cnt_roll_28 = (feats_df[(feats_df.dteday >= start_date) &
                                          (feats_df.dteday <= end_date)][TARGET].mean())

        # Check that build_features produces the same value
        feats = build_features(feats_df)
>       actual = feats.set_index("dteday").cnt_roll_28[target_date]
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_leakage.py:75: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self =             instant  season      yr  ... cnt_lag_1 cnt_lag_7   cnt_roll_7
dteday                               ...    ... 1787.0  1530.142857
2012-12-31    731.0  WINTER  2012.0  ...    1796.0     920.0  1531.428571

[714 rows x 27 columns]
name = 'cnt_roll_28'

    @final
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'DataFrame' object has no attribute 'cnt_roll_28'. Did you mean: 'cnt_roll_7'?

.venv/lib/python3.12/site-packages/pandas/core/generic.py:6194: AttributeError
================ short test summary =============
FAILED tests/test_leakage.py::test_cnt_roll_28_matches_hand_computed - Attrib...
1 failed in 0.52s
```

## (a) forbidden column leaks into features: in src/features.py, change the last line of feature_columns to return [c for c in numeric if c not in FORBIDDEN] + ["casual"]

```
On branch sidd-work
Your branch is up to date with 'origin/sidd-work'.

Changes not staged for commit:
  (use "git add <file>..." to update the status)
  (use "git restore <file>" to discard changes in working directory)
	modified:   src/features.py

no changes added to commit (use "git add" and/or "git commit -a")
```

```
Exit code 1
.....F.........                                                          [100%]
=================================== FAILURES ===================================
__________________________ test_no_forbidden_features __________________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7  cnt_roll_28
0   2011-01-31     31.0  WINTER  ...     141....142857  4071.321429
671 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  3969.428571

[672 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_28', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:32: AssertionError
================ short test summary =============
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 14 passed in 1.87s
```

```
diff --git a/src/features.py b/src/features.py
index 5756750..d890b06 100644
--- a/src/features.py
+++ b/src/features.py
@@ -84,7 +84,7 @@ def build_features(df: pd.DataFrame) -> pd.DataFrame:
 def feature_columns(df: pd.DataFrame) -> list[str]:
     """Numeric columns that are safe to feed the model."""
     numeric = df.select_dtypes(include="number").columns
-    return [c for c in numeric if c not in FORBIDDEN]
+    return [c for c in numeric if c not in FORBIDDEN] + ["casual"]


if __name__ == "__main__":

```

## Fault (b): .shift(1) deleted from cnt_roll_7

### Exact change
```diff
diff --git a/src/features.py b/src/features.py
index 5756750..5c88fd5 100644
--- a/src/features.py
+++ b/src/features.py
@@ -75,7 +75,7 @@ def build_features(df: pd.DataFrame) -> pd.DataFrame:
     # If you add a longer lag, raise LAG_WARMUP in src/config.py.
     out["cnt_lag_1"] = out[TARGET].shift(1)
     out["cnt_lag_7"] = out[TARGET].shift(7)
-    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(7).mean()
+    out["cnt_roll_7"] = out[TARGET].rolling(7).mean()
     out["cnt_roll_28"] = out[TARGET].shift(1).rolling(28).mean()
 
     return out.dropna().reset_index(drop=True)
```

### Red test output
```
[672 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4605.285714285715) == 4724.428571428572 ± 0.00472443
E             
E             comparison failed
E             Obtained: 4605.285714285715
E             Expected: 4724.428571428572 ± 0.00472443

tests/test_leakage.py:58: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 14 passed in 2.77s
```

### Hook stderr
```
PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/siddhusarvepally/Downloads/bikeshare-open/src/features.py:
[672 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4605.285714285715) == 4724.428571428572 ± 0.00472443
E
E             comparison failed
E             Obtained: 4605.285714285715
E             Expected: 4724.428571428572 ± 0.00472443

tests/test_leakage.py:58: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 7 passed in 0.75s
```

Turns to fix: 1. The agent first chased a stale "# broken for testing" comment in src/config.py before reading the failing test and restoring .shift(1).

## Fault (c): raise removed from encode_weather

Before this fault, no test exercised encode_weather. Removing the raise left all 15 tests green and the hook silent, because the real data contains only GOOD, MISTY, and BAD. I added test_encode_weather_raises_on_unknown_label (its own commit) and then reseeded the fault.

When asked through /seed-fault, the agent over-edited: it deleted the return line as well, so encode_weather returned None and five tests failed. I reverted that and seeded the two intended lines by hand. The hook stderr below is from running the hook on that edit.

### Exact change
```diff
diff --git a/src/features.py b/src/features.py
index 5756750..dd25e0f 100644
--- a/src/features.py
+++ b/src/features.py
@@ -28,8 +28,6 @@ def encode_weather(series: pd.Series) -> pd.Series:
     """
     known = series.dropna()
     unknown = set(known.unique()) - set(WEATHER_ORDER)
-    if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
     return series.map(WEATHER_ORDER).astype(float)
 
 
```

### Red test output
```
............F...                                                         [100%]
=================================== FAILURES ===================================
_________________ test_encode_weather_raises_on_unknown_label __________________

    def test_encode_weather_raises_on_unknown_label():
        """An unseen weather label must fail loudly, not become NaN and be
        silently dropped by dropna()."""
>       with pytest.raises(ValueError, match="unmapped"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:99: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_encode_weather_raises_on_unknown_label - F...
1 failed, 15 passed in 1.25s
```

### Hook stderr
```
Leakage tests failed after editing /Users/siddhusarvepally/Downloads/bikeshare-open/src/features.py:
........F                                                                [100%]
=================================== FAILURES ===================================
_________________ test_encode_weather_raises_on_unknown_label __________________

    def test_encode_weather_raises_on_unknown_label():
        """An unseen weather label must fail loudly, not become NaN and be
        silently dropped by dropna()."""
>       with pytest.raises(ValueError, match="unmapped"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:99: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_encode_weather_raises_on_unknown_label - F...
1 failed, 8 passed in 0.24s
```

Turns to fix: 1
