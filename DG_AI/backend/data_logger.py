"""
DrainGuard AI - Data Logger
Consumes sensor readings from a queue and logs them to CSV files.
Supports file rotation and thread-safe operation.
"""

import os
import csv
import threading
import logging
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import LIVE_DATA_CSV, ALERT_LOG_CSV, DATA_DIR

logger = logging.getLogger(__name__)

CSV_HEADERS = ["timestamp", "water_level_cm", "gas_level", "is_anomaly", "anomaly_type",
               "risk_score", "risk_level"]
ALERT_HEADERS = ["timestamp", "anomaly_type", "risk_score", "risk_level",
                 "water_level_cm", "gas_level", "message"]

MAX_LIVE_ROWS = 10000  # Rotate after this many rows


class DataLogger:
    """Thread-safe CSV logger for sensor data and alerts."""

    def __init__(self, live_csv=LIVE_DATA_CSV, alert_csv=ALERT_LOG_CSV):
        self.live_csv = live_csv
        self.alert_csv = alert_csv
        self._lock = threading.Lock()
        self._row_count = 0
        self._alert_count = 0
        self._initialize_files()

    def _initialize_files(self):
        """Create CSV files with headers if they don't exist."""
        os.makedirs(DATA_DIR, exist_ok=True)

        if not os.path.exists(self.live_csv):
            with open(self.live_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
            logger.info(f"Created {self.live_csv}")

        if not os.path.exists(self.alert_csv):
            with open(self.alert_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(ALERT_HEADERS)
            logger.info(f"Created {self.alert_csv}")

        # Count existing rows
        try:
            with open(self.live_csv, 'r') as f:
                self._row_count = sum(1 for _ in f) - 1  # Minus header
        except Exception:
            self._row_count = 0

    def log_reading(self, reading: dict):
        """Log a sensor reading to the live CSV."""
        with self._lock:
            # Check for rotation
            if self._row_count >= MAX_LIVE_ROWS:
                self._rotate_file()

            row = [
                reading.get("timestamp", datetime.now().isoformat()),
                reading.get("water_level_cm", 0),
                reading.get("gas_level", 0),
                reading.get("is_anomaly", 0),
                reading.get("anomaly_type", "NORMAL"),
                reading.get("risk_score", 0),
                reading.get("risk_level", "NORMAL"),
            ]

            with open(self.live_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)

            self._row_count += 1

    def log_alert(self, alert: dict):
        """Log an anomaly alert."""
        with self._lock:
            row = [
                alert.get("timestamp", datetime.now().isoformat()),
                alert.get("anomaly_type", "UNKNOWN"),
                alert.get("risk_score", 0),
                alert.get("risk_level", "UNKNOWN"),
                alert.get("water_level_cm", 0),
                alert.get("gas_level", 0),
                alert.get("message", ""),
            ]

            with open(self.alert_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)

            self._alert_count += 1
            logger.warning(f"ALERT: {alert.get('anomaly_type')} - Risk: {alert.get('risk_score')}%")

    def _rotate_file(self):
        """Rotate the live CSV when it gets too large."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(DATA_DIR, f"live_data_archive_{timestamp}.csv")

        try:
            os.rename(self.live_csv, archive_path)
            logger.info(f"Rotated live data to {archive_path}")
        except OSError as e:
            logger.error(f"Rotation failed: {e}")

        # Create fresh file
        with open(self.live_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        self._row_count = 0

    def clear_live_data(self):
        """Clear the live data file (for dashboard reset)."""
        with self._lock:
            with open(self.live_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
            self._row_count = 0
            logger.info("Live data cleared")

    @property
    def stats(self):
        return {
            "live_rows": self._row_count,
            "alert_count": self._alert_count,
        }
