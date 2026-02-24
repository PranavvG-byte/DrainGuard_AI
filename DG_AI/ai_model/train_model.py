"""
DrainGuard AI - Model Training
Trains Isolation Forest with engineered features on synthetic sensor data.

Usage:
    python ai_model/train_model.py
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    SENSOR_DATA_CSV, MODEL_PATH, MODEL_DIR,
    ISOLATION_FOREST_ESTIMATORS,
    ISOLATION_FOREST_CONTAMINATION,
    FEATURE_ROLLING_WINDOW,
)


def engineer_features(df: pd.DataFrame, window: int = FEATURE_ROLLING_WINDOW) -> pd.DataFrame:
    """
    Create time-series features from raw sensor data.
    
    Features:
    - water_level_cm, gas_level (raw)
    - water_rolling_mean, water_rolling_std (trend & volatility)
    - gas_rolling_mean, gas_rolling_std
    - water_delta (rate of change)
    - gas_delta
    - water_gas_ratio (interaction term)
    """
    features = pd.DataFrame()

    features["water_level_cm"] = df["water_level_cm"]
    features["gas_level"] = df["gas_level"]

    # Rolling statistics
    features["water_rolling_mean"] = df["water_level_cm"].rolling(window, min_periods=1).mean()
    features["water_rolling_std"] = df["water_level_cm"].rolling(window, min_periods=1).std().fillna(0)
    features["gas_rolling_mean"] = df["gas_level"].rolling(window, min_periods=1).mean()
    features["gas_rolling_std"] = df["gas_level"].rolling(window, min_periods=1).std().fillna(0)

    # Rate of change (delta)
    features["water_delta"] = df["water_level_cm"].diff().fillna(0)
    features["gas_delta"] = df["gas_level"].diff().fillna(0)

    # Interaction feature
    features["water_gas_ratio"] = (
        df["water_level_cm"] / (df["gas_level"].replace(0, 1))
    )

    return features


def train_model():
    """Train the Isolation Forest model and save to disk."""
    print("=" * 60)
    print("  DrainGuard AI - Model Training")
    print("=" * 60)

    # Load data
    print(f"\n[1/4] Loading data from {SENSOR_DATA_CSV}...")
    df = pd.read_csv(SENSOR_DATA_CSV)
    print(f"      Loaded {len(df)} samples ({df['is_anomaly'].sum()} labeled anomalies)")

    # Feature engineering
    print("[2/4] Engineering features...")
    features = engineer_features(df)
    feature_names = list(features.columns)
    print(f"      Features: {feature_names}")

    # Scale features
    scaler = StandardScaler()
    X = scaler.fit_transform(features.values)

    # Train Isolation Forest
    print(f"[3/4] Training IsolationForest (n_estimators={ISOLATION_FOREST_ESTIMATORS}, "
          f"contamination={ISOLATION_FOREST_CONTAMINATION})...")

    model = IsolationForest(
        n_estimators=ISOLATION_FOREST_ESTIMATORS,
        contamination=ISOLATION_FOREST_CONTAMINATION,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X)

    # Predictions on training data for evaluation
    predictions = model.predict(X)
    anomaly_count = (predictions == -1).sum()
    anomaly_pct = 100 * anomaly_count / len(predictions)

    # Anomaly scores (lower = more anomalous)
    scores = model.decision_function(X)

    print(f"      Detected anomalies: {anomaly_count} ({anomaly_pct:.1f}%)")
    print(f"      Score range: [{scores.min():.4f}, {scores.max():.4f}]")
    print(f"      Score mean: {scores.mean():.4f}, std: {scores.std():.4f}")

    # Compare with ground truth labels
    true_anomalies = df["is_anomaly"].values
    true_positive = ((predictions == -1) & (true_anomalies == 1)).sum()
    false_positive = ((predictions == -1) & (true_anomalies == 0)).sum()
    false_negative = ((predictions == 1) & (true_anomalies == 1)).sum()

    if (true_positive + false_positive) > 0:
        precision = true_positive / (true_positive + false_positive)
    else:
        precision = 0
    if (true_positive + false_negative) > 0:
        recall = true_positive / (true_positive + false_negative)
    else:
        recall = 0

    print(f"\n      vs Ground Truth:")
    print(f"        True Positives:  {true_positive}")
    print(f"        False Positives: {false_positive}")
    print(f"        False Negatives: {false_negative}")
    print(f"        Precision:       {precision:.3f}")
    print(f"        Recall:          {recall:.3f}")

    # Save model + scaler + metadata
    print(f"\n[4/4] Saving model to {MODEL_PATH}...")
    os.makedirs(MODEL_DIR, exist_ok=True)

    model_package = {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_names,
        "rolling_window": FEATURE_ROLLING_WINDOW,
        "score_threshold": float(np.percentile(scores, 5)),  # 5th percentile as threshold
        "training_stats": {
            "samples": len(df),
            "anomalies_detected": int(anomaly_count),
            "precision": float(precision),
            "recall": float(recall),
            "score_mean": float(scores.mean()),
            "score_std": float(scores.std()),
        }
    }

    joblib.dump(model_package, MODEL_PATH)
    print(f"      Model saved successfully!")
    print(f"\n{'=' * 60}\n")

    return model_package


if __name__ == "__main__":
    train_model()
