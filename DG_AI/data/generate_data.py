"""
DrainGuard AI – Synthetic Sensor Data Generator
Generates realistic training data with injected anomalies for Isolation Forest.

Usage:
    python data/generate_data.py
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


from config.settings import (
    SENSOR_DATA_CSV, DATA_DIR,
    WATER_LEVEL_NORMAL_LOW, WATER_LEVEL_NORMAL_HIGH,
    WATER_BLOCKAGE_THRESHOLD, WATER_LEAKAGE_THRESHOLD,
    GAS_NORMAL_MAX, GAS_DANGER_THRESHOLD,
    SIMULATOR_ANOMALY_RATE
)

# ─── Configuration ────────────────────────────────────────────────────────────
NUM_SAMPLES = 5000
SAMPLE_INTERVAL_SECONDS = 30   # 30-second intervals → ~41 hours of data
SEED = 42

# ─── Anomaly Injection Profiles ──────────────────────────────────────────────
ANOMALY_PROFILES = {
    "blockage": {
        "water_level_range": (2.0, WATER_BLOCKAGE_THRESHOLD),
        "gas_level_range": (300, 900),   # Slight gas increase with stagnation
        "duration": (5, 20),             # Burst length in samples
        "probability": 0.25,
    },
    "leakage": {
        "water_level_range": (WATER_LEAKAGE_THRESHOLD, 180.0),
        "gas_level_range": (100, 500),
        "duration": (3, 15),
        "probability": 0.20,
    },
    "gas_hazard": {
        "water_level_range": (15.0, 50.0),
        "gas_level_range": (GAS_DANGER_THRESHOLD, 3800),
        "duration": (5, 25),
        "probability": 0.25,
    },
    "flood_risk": {
        "water_level_range": (1.0, 8.0),   # Very high water (low distance)
        "gas_level_range": (800, 2000),
        "duration": (10, 30),
        "probability": 0.30,
    },
}


def generate_normal_data(n: int, rng: np.random.Generator) -> tuple:
    """Generate normal operating sensor data with realistic noise."""
    # Water level: sinusoidal daily pattern + noise (simulates tidal/usage cycles)
    t = np.linspace(0, 8 * np.pi, n)
    water_base = (WATER_LEVEL_NORMAL_LOW + WATER_LEVEL_NORMAL_HIGH) / 2
    water_amplitude = (WATER_LEVEL_NORMAL_HIGH - WATER_LEVEL_NORMAL_LOW) / 3
    water_level = (
        water_base
        + water_amplitude * np.sin(t)
        + rng.normal(0, 2.0, n)  # ±2cm jitter
    )
    water_level = np.clip(water_level, 5.0, 90.0)

    # Gas level: mostly stable with occasional mild fluctuations
    gas_base = 400.0
    gas_level = (
        gas_base
        + 100 * np.sin(t * 0.7)
        + rng.normal(0, 50.0, n)  # ±50 ADC noise
    )
    gas_level = np.clip(gas_level, 100, GAS_NORMAL_MAX + 100).astype(int)

    return water_level, gas_level


def inject_anomalies(
    water_level: np.ndarray,
    gas_level: np.ndarray,
    rng: np.random.Generator,
    target_anomaly_rate: float = SIMULATOR_ANOMALY_RATE,
) -> np.ndarray:
    """Inject realistic anomaly bursts into sensor data."""
    n = len(water_level)
    is_anomaly = np.zeros(n, dtype=int)
    total_anomaly_target = int(n * target_anomaly_rate)
    anomaly_count = 0
    i = 0

    while i < n and anomaly_count < total_anomaly_target:
        if rng.random() < 0.03 and is_anomaly[i] == 0:
            # Pick a random anomaly profile
            profile_name = rng.choice(list(ANOMALY_PROFILES.keys()))
            profile = ANOMALY_PROFILES[profile_name]

            # Determine burst duration
            burst_len = rng.integers(profile["duration"][0], profile["duration"][1] + 1)
            end = min(i + burst_len, n)

            # Inject anomaly with gradual onset (ramp-in over first 30% of burst)
            ramp = end - i
            ramp_in = max(1, int(ramp * 0.3))

            for j in range(i, end):
                if anomaly_count >= total_anomaly_target:
                    break  # Guard against overshooting the target rate

                progress = min(1.0, (j - i) / ramp_in)

                # Blend from normal toward anomalous values
                target_water = rng.uniform(*profile["water_level_range"])
                target_gas = rng.uniform(*profile["gas_level_range"])

                water_level[j] = (1 - progress) * water_level[j] + progress * target_water
                gas_level[j] = int((1 - progress) * gas_level[j] + progress * target_gas)

                is_anomaly[j] = 1
                anomaly_count += 1

            i = end + rng.integers(20, 60)  # Gap before next anomaly
        else:
            i += 1

    return is_anomaly


def generate_dataset():
    """Generate the full synthetic dataset and save to CSV."""
    rng = np.random.default_rng(SEED)

    print("=" * 60)
    print("  DrainGuard AI – Synthetic Data Generator")
    print("=" * 60)

    # Generate timestamps
    start_time = datetime(2026, 2, 1, 0, 0, 0)
    timestamps = [start_time + timedelta(seconds=i * SAMPLE_INTERVAL_SECONDS)
                  for i in range(NUM_SAMPLES)]

    # Generate base sensor data
    print(f"\n[1/3] Generating {NUM_SAMPLES} normal sensor readings...")
    water_level, gas_level = generate_normal_data(NUM_SAMPLES, rng)

    # Inject anomalies
    print("[2/3] Injecting anomaly patterns...")
    is_anomaly = inject_anomalies(water_level, gas_level, rng)

    # Build DataFrame
    df = pd.DataFrame({
        "timestamp": timestamps,
        "water_level_cm": np.round(water_level, 2),
        "gas_level": gas_level.astype(int),
        "is_anomaly": is_anomaly,
    })

    # Save
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(SENSOR_DATA_CSV, index=False)

    # Statistics
    anomaly_count = df["is_anomaly"].sum()
    anomaly_pct = 100 * anomaly_count / len(df)

    print(f"[3/3] Saved to: {SENSOR_DATA_CSV}")
    print(f"\n{'-' * 40}")
    print(f"  Total samples:    {len(df):,}")
    print(f"  Anomalies:        {anomaly_count:,} ({anomaly_pct:.1f}%)")
    print(f"  Water level range: {df['water_level_cm'].min():.1f} - {df['water_level_cm'].max():.1f} cm")
    print(f"  Gas level range:   {df['gas_level'].min()} - {df['gas_level'].max()}")
    print(f"  Time span:         {df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]}")
    print(f"{'-' * 40}\n")

    return df


if __name__ == "__main__":
    generate_dataset()
