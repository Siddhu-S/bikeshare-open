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
