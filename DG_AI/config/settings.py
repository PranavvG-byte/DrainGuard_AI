"""
DrainGuard AI – Central Configuration
All system constants, thresholds, and paths consolidated here.
"""

import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "ai_model")
LOG_DIR = os.path.join(BASE_DIR, "logs")

SENSOR_DATA_CSV = os.path.join(DATA_DIR, "sensor_data.csv")
LIVE_DATA_CSV = os.path.join(DATA_DIR, "live_data.csv")
ALERT_LOG_CSV = os.path.join(DATA_DIR, "alert_log.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")

# ─── Serial / Hardware ───────────────────────────────────────────────────────
SERIAL_PORT = "COM3"           # Change to match your ESP32 port
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 2             # seconds

# ─── Sensor Thresholds ──────────────────────────────────────────────────────
# Water Level (cm) – measured as distance from sensor to water surface
WATER_LEVEL_MIN = 0.0          # Physical minimum
WATER_LEVEL_MAX = 200.0        # Physical maximum
WATER_LEVEL_NORMAL_LOW = 20.0  # Normal operating range
WATER_LEVEL_NORMAL_HIGH = 60.0
WATER_BLOCKAGE_THRESHOLD = 10.0   # Below this = blockage warning
WATER_LEAKAGE_THRESHOLD = 100.0   # Above this = leakage warning

# Gas Level (ADC 0-4095 for ESP32 12-bit)
GAS_LEVEL_MIN = 0
GAS_LEVEL_MAX = 4095
GAS_NORMAL_MAX = 800
GAS_WARNING_THRESHOLD = 1500
GAS_DANGER_THRESHOLD = 2500

# ─── AI Model Hyperparameters ────────────────────────────────────────────────
ISOLATION_FOREST_ESTIMATORS = 200
ISOLATION_FOREST_CONTAMINATION = 0.08
FEATURE_ROLLING_WINDOW = 10       # Window size for rolling stats
ANOMALY_COOLDOWN_SECONDS = 60     # Suppress repeated alerts within this window

# ─── Risk Classification ─────────────────────────────────────────────────────
RISK_LEVELS = {
    "NORMAL":      {"color": "#22c55e", "min_score": 0,  "max_score": 25},
    "LOW":         {"color": "#eab308", "min_score": 25, "max_score": 50},
    "MODERATE":    {"color": "#f97316", "min_score": 50, "max_score": 75},
    "HIGH":        {"color": "#ef4444", "min_score": 75, "max_score": 90},
    "CRITICAL":    {"color": "#dc2626", "min_score": 90, "max_score": 100},
}

RISK_TYPES = [
    "NORMAL",
    "BLOCKAGE",
    "LEAKAGE",
    "GAS_HAZARD",
    "FLOOD_RISK",
]

# ─── Simulator ────────────────────────────────────────────────────────────────
SIMULATOR_INTERVAL = 1.0          # Seconds between simulated readings
SIMULATOR_ANOMALY_RATE = 0.08     # 8% chance of anomaly per reading
SIMULATOR_BURST_DURATION = 10     # Number of readings in an anomaly burst

# ─── Dashboard ────────────────────────────────────────────────────────────────
DASHBOARD_REFRESH_SECONDS = 2
DASHBOARD_MAX_POINTS = 200        # Max data points shown on live charts
DASHBOARD_THEME = "dark"
