"""
DrainGuard AI - Serial Reader
Reads JSON sensor data from ESP32 via USB serial port.

Provides a thread-safe queue interface for downstream consumers.
"""

import json
import time
import threading
import queue
import logging
from datetime import datetime

import serial

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SERIAL_PORT, SERIAL_BAUD, SERIAL_TIMEOUT

logger = logging.getLogger(__name__)


class SerialReader:
    """Reads JSON data from ESP32 serial port and pushes to a queue."""

    def __init__(self, port=SERIAL_PORT, baud=SERIAL_BAUD, timeout=SERIAL_TIMEOUT):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.data_queue = queue.Queue(maxsize=1000)
        self._running = False
        self._thread = None
        self._ser = None
        self._error_count = 0
        self._read_count = 0

    def start(self):
        """Start the serial reader in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        logger.info(f"Serial reader started on {self.port} @ {self.baud} baud")

    def stop(self):
        """Stop the serial reader."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self._ser and self._ser.is_open:
            self._ser.close()
        logger.info("Serial reader stopped")

    def _read_loop(self):
        """Main read loop - connects to serial and parses JSON lines."""
        while self._running:
            try:
                if self._ser is None or not self._ser.is_open:
                    self._connect()

                line = self._ser.readline()
                if not line:
                    continue

                line_str = line.decode('utf-8', errors='ignore').strip()
                if not line_str:
                    continue

                # Parse JSON
                data = json.loads(line_str)

                # Skip boot/event messages
                if "event" in data:
                    logger.info(f"ESP32 event: {data}")
                    continue

                # Validate required fields
                if "water_level" not in data or "gas_level" not in data:
                    self._error_count += 1
                    continue

                # Validate ranges
                water = data["water_level"]
                gas = data["gas_level"]

                if water < -1 or water > 500 or gas < 0 or gas > 4095:
                    logger.warning(f"Out-of-range reading: water={water}, gas={gas}")
                    self._error_count += 1
                    continue

                # Add timestamp and push to queue
                data["timestamp"] = datetime.now().isoformat()
                data["water_level_cm"] = round(water, 2)

                try:
                    self.data_queue.put_nowait(data)
                    self._read_count += 1
                except queue.Full:
                    # Drop oldest if full
                    self.data_queue.get_nowait()
                    self.data_queue.put_nowait(data)

            except json.JSONDecodeError:
                self._error_count += 1
                continue
            except serial.SerialException as e:
                logger.error(f"Serial error: {e}")
                self._ser = None
                time.sleep(2)  # Wait before reconnect
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(1)

    def _connect(self):
        """Establish serial connection with retry."""
        while self._running:
            try:
                self._ser = serial.Serial(
                    port=self.port,
                    baudrate=self.baud,
                    timeout=self.timeout
                )
                logger.info(f"Connected to {self.port}")
                time.sleep(2)  # Wait for ESP32 boot message
                return
            except serial.SerialException:
                logger.warning(f"Cannot open {self.port}, retrying in 3s...")
                time.sleep(3)

    @property
    def stats(self):
        return {
            "readings": self._read_count,
            "errors": self._error_count,
            "queue_size": self.data_queue.qsize(),
            "connected": self._ser is not None and self._ser.is_open,
        }
