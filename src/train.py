"""Stage 3: train models and evaluate."""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score

from src.config import METRICS, PROCESSED, TARGET, TRAIN_END, VALID_END


MODELS = {
    "baseline_mean": lambda y: np.full_like(y, float(np.mean(y))),
    "baseline_persistence": lambda y: np.roll(y, 1),
    "ridge": Ridge(alpha=1.0),
    "hgb": GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42),
}


def temporal_split(df: pd.DataFrame):
    """Split into train (2011), valid (H1 2012), test (H2 2012).

    The function ensures no random split ever leaks forward-looking info.
    """
    df = df.copy()
    df["dteday"] = pd.to_datetime(df["dteday"])
    df["year"] = df["dteday"].dt.year
    df["month"] = df["dteday"].dt.month

    train = df[df.year == 2011].copy()
    valid = df[(df.year == 2012) & (df.month <= 6)]
    test = df[(df.year == 2012) & (df.month > 6)]

    return train.reset_index(drop=True), valid.reset_index(drop=True), test.reset_index(drop=True)


from src.features import feature_columns


def evaluate(df: pd.DataFrame):
    """Train all models on train+valid and report on valid and test."""
    cols = feature_columns(df)

    train, valid, test = temporal_split(df)
    train_full = pd.concat([train, valid], ignore_index=True)

    # Train on train + valid, evaluate on both valid and test
    y_train = train_full[TARGET].astype(float)
    X_train = train_full[cols]
    y_valid = valid[TARGET].astype(float)
    y_test = test[TARGET].astype(float)
    X_valid = valid[cols]
    X_test = test[cols]

    results = {}

    for name, model in MODELS.items():
        if callable(model):
            # Baseline models: predict on train_full, then evaluate each set separately
            preds_full = model(y_train)

            # For baseline_mean: it's a constant, so same prediction everywhere
            if name == "baseline_mean":
                y_mean = float(np.mean(y_train))
                results[name] = {
                    "valid": {"r2": r2_score(y_valid, np.full_like(y_valid, y_mean)),
                              "mae": mean_absolute_error(y_valid, np.full_like(y_valid, y_mean))},
                    "test": {"r2": r2_score(y_test, np.full_like(y_test, y_mean)),
                             "mae": mean_absolute_error(y_test, np.full_like(y_test, y_mean))}
                }
            # For baseline_persistence: split the predictions by valid/test length
            else:
                n_valid = len(y_valid)
                valid_preds = preds_full[:n_valid]
                test_preds = preds_full[n_valid:]
                results[name] = {
                    "valid": {"r2": r2_score(y_valid, valid_preds),
                              "mae": mean_absolute_error(y_valid, valid_preds)},
                    "test": {"r2": r2_score(y_test, test_preds),
                             "mae": mean_absolute_error(y_test, test_preds)}
                }
        else:
            # Ridge needs both X and y
            model.fit(X_train, y_train)
            valid_preds = model.predict(X_valid)
            test_preds = model.predict(X_test)
            results[name] = {
                "valid": {"r2": r2_score(y_valid, valid_preds), "mae": mean_absolute_error(y_valid, valid_preds)},
                "test": {"r2": r2_score(y_test, test_preds), "mae": mean_absolute_error(y_test, test_preds)}
            }

    return results


if __name__ == "__main__":
    data = pd.read_parquet(PROCESSED)
    metrics = evaluate(data)

    print(json.dumps(metrics, indent=2))

