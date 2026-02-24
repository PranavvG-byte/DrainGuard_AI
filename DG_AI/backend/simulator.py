"""
DrainGuard AI - Sensor Simulator
Generates realistic fake sensor data for demo/testing without ESP32 hardware.

Provides the same queue-based interface as SerialReader.
"""

import time
import queue
import threading
import logging
import numpy as np
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    SIMULATOR_INTERVAL,
    SIMULATOR_ANOMALY_RATE,
    SIMULATOR_BURST_DURATION,
    WATER_LEVEL_NORMAL_LOW,
    WATER_LEVEL_NORMAL_HIGH,
    WATER_BLOCKAGE_THRESHOLD,
    WATER_LEAKAGE_THRESHOLD,
    GAS_NORMAL_MAX,
    GAS_DANGER_THRESHOLD,
)

logger = logging.getLogger(__name__)


class SensorSimulator:
    """Generates realistic sensor data with controllable anomaly injection."""

    def __init__(self, interval=SIMULATOR_INTERVAL, anomaly_rate=SIMULATOR_ANOMALY_RATE):
        self.interval = interval
        self.anomaly_rate = anomaly_rate
        self.data_queue = queue.Queue(maxsize=1000)
        self._running = False
        self._thread = None
        self._read_count = 0
        self._inject_anomaly = False  # Manual anomaly trigger
        self._anomaly_burst_remaining = 0
        self._current_anomaly_type = None
        self._rng = np.random.default_rng()

    def start(self):
        """Start the simulator in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._generate_loop, daemon=True)
        self._thread.start()
        logger.info(f"Sensor simulator started (interval={self.interval}s)")

    def stop(self):
        """Stop the simulator."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Sensor simulator stopped")

    def trigger_anomaly(self, anomaly_type=None):
        """Manually trigger an anomaly burst for demo purposes."""
        self._inject_anomaly = True
        self._current_anomaly_type = anomaly_type
        logger.info(f"Anomaly triggered: {anomaly_type or 'random'}")

    def _generate_loop(self):
        """Main data generation loop."""
        phase = 0.0
        while self._running:
            try:
                phase += 0.05
                reading = self._generate_reading(phase)

                try:
                    self.data_queue.put_nowait(reading)
                    self._read_count += 1
                except queue.Full:
                    self.data_queue.get_nowait()
                    self.data_queue.put_nowait(reading)

                time.sleep(self.interval)

            except Exception as e:
                logger.error(f"Simulator error: {e}")
                time.sleep(1)

    def _generate_reading(self, phase):
        """Generate a single sensor reading."""
        is_anomaly = False

        # Check for anomaly burst
        if self._anomaly_burst_remaining > 0:
            water, gas = self._generate_anomaly_values()
            self._anomaly_burst_remaining -= 1
            is_anomaly = True
        elif self._inject_anomaly or self._rng.random() < self.anomaly_rate * 0.1:
            # Start new anomaly burst
            self._start_anomaly_burst()
            water, gas = self._generate_anomaly_values()
            is_anomaly = True
            self._inject_anomaly = False
        else:
            # Normal readings
            water, gas = self._generate_normal_values(phase)

        return {
            "timestamp": datetime.now().isoformat(),
            "water_level_cm": round(float(water), 2),
            "gas_level": int(gas),
            "is_anomaly": int(is_anomaly),
            "anomaly_type": self._current_anomaly_type if is_anomaly else "NORMAL",
        }

    def _generate_normal_values(self, phase):
        """Generate normal sensor values with realistic patterns."""
        water_base = (WATER_LEVEL_NORMAL_LOW + WATER_LEVEL_NORMAL_HIGH) / 2
        water_amplitude = (WATER_LEVEL_NORMAL_HIGH - WATER_LEVEL_NORMAL_LOW) / 3
        water = water_base + water_amplitude * np.sin(phase) + self._rng.normal(0, 2.0)
        water = np.clip(water, 8.0, 85.0)

        gas = 400 + 80 * np.sin(phase * 0.7) + self._rng.normal(0, 40)
        gas = np.clip(gas, 100, GAS_NORMAL_MAX)

        return water, gas

    def _start_anomaly_burst(self):
        """Initialize an anomaly burst."""
        anomaly_types = ["BLOCKAGE", "LEAKAGE", "GAS_HAZARD", "FLOOD_RISK"]
        if self._current_anomaly_type and self._current_anomaly_type in anomaly_types:
            pass  # Keep manual selection
        else:
            self._current_anomaly_type = self._rng.choice(anomaly_types)

        self._anomaly_burst_remaining = self._rng.integers(
            SIMULATOR_BURST_DURATION // 2,
            SIMULATOR_BURST_DURATION + 1
        )

    def _generate_anomaly_values(self):
        """Generate anomalous sensor values based on current anomaly type."""
        rng = self._rng

        if self._current_anomaly_type == "BLOCKAGE":
            water = rng.uniform(2.0, WATER_BLOCKAGE_THRESHOLD)
            gas = rng.uniform(300, 900)
        elif self._current_anomaly_type == "LEAKAGE":
            water = rng.uniform(WATER_LEAKAGE_THRESHOLD, 160.0)
            gas = rng.uniform(200, 600)
        elif self._current_anomaly_type == "GAS_HAZARD":
            water = rng.uniform(20.0, 55.0)
            gas = rng.uniform(GAS_DANGER_THRESHOLD, 3800)
        elif self._current_anomaly_type == "FLOOD_RISK":
            water = rng.uniform(1.0, 8.0)
            gas = rng.uniform(800, 2000)
        else:
            water = rng.uniform(5.0, 90.0)
            gas = rng.uniform(100, 3000)

        return water, gas

    @property
    def stats(self):
        return {
            "readings": self._read_count,
            "queue_size": self.data_queue.qsize(),
            "anomaly_active": self._anomaly_burst_remaining > 0,
            "current_anomaly_type": self._current_anomaly_type,
        }
