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
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

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
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_cnt_roll_28_matches_hand_computed - Attrib...
1 failed in 0.52s
```
