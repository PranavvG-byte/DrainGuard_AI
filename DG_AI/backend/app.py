"""
DrainGuard AI - Backend Application Entry Point
Orchestrates data source, AI inference, and logging.

Usage:
    python backend/app.py --mode simulator    # Run with simulated data (no hardware)
    python backend/app.py --mode serial       # Run with ESP32 hardware
"""

import time
import argparse
import logging
import threading
from datetime import datetime


from config.settings import LIVE_DATA_CSV, ALERT_LOG_CSV
from backend.simulator import SensorSimulator
from backend.data_logger import DataLogger
from ai_model.anomaly_detection import AnomalyDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DrainGuard")


def run_inference_loop(data_source, data_logger, detector, stop_event):
    """
    Main inference loop: read from data source -> AI predict -> log results.
    """
    logger.info("Inference loop started")

    while not stop_event.is_set():
        try:
            # Get reading from data source (simulator or serial reader)
            if data_source.data_queue.empty():
                time.sleep(0.1)
                continue

            reading = data_source.data_queue.get(timeout=1)

            # Run AI prediction
            result = detector.predict(
                water_level=reading["water_level_cm"],
                gas_level=reading["gas_level"],
            )

            # Merge reading with AI results
            enriched = {
                **reading,
                "risk_score": result["risk_score"],
                "risk_level": result["risk_level"],
                "is_anomaly": int(result["is_anomaly"]),
                "anomaly_type": result["risk_type"],
            }

            # Log to CSV
            data_logger.log_reading(enriched)

            # Log alerts
            if result["is_anomaly"] and not result.get("alert_suppressed", False):
                alert = {
                    **enriched,
                    "message": result["details"],
                }
                data_logger.log_alert(alert)
                logger.warning(
                    f"[ALERT] {result['risk_type']} | "
                    f"Risk: {result['risk_score']}% | "
                    f"Water: {reading['water_level_cm']}cm | "
                    f"Gas: {reading['gas_level']}"
                )

        except Exception as e:
            logger.error(f"Inference error: {e}")
            time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description="DrainGuard AI Backend")
    parser.add_argument(
        "--mode",
        choices=["simulator", "serial"],
        default="simulator",
        help="Data source mode (default: simulator)",
    )
    parser.add_argument(
        "--port",
        default=None,
        help="Serial port (for serial mode, e.g., COM3)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  DrainGuard AI - Backend Service")
    print(f"  Mode: {args.mode.upper()}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Initialize components
    logger.info("Initializing components...")

    # Data source
    if args.mode == "simulator":
        data_source = SensorSimulator()
    else:
        from backend.serial_reader import SerialReader
        port = args.port or "COM3"
        data_source = SerialReader(port=port)

    # Logger and detector
    data_logger = DataLogger()
    detector = AnomalyDetector()

    # Clear previous live data for fresh session
    data_logger.clear_live_data()

    # Start data source
    data_source.start()
    logger.info(f"Data source ({args.mode}) started")

    # Start inference loop in background thread
    stop_event = threading.Event()
    inference_thread = threading.Thread(
        target=run_inference_loop,
        args=(data_source, data_logger, detector, stop_event),
        daemon=True,
    )
    inference_thread.start()

    # Main thread: status reporting
    try:
        while True:
            time.sleep(10)
            src_stats = data_source.stats
            log_stats = data_logger.stats
            det_stats = detector.stats

            logger.info(
                f"[STATUS] Readings: {src_stats.get('readings', 0)} | "
                f"Logged: {log_stats['live_rows']} | "
                f"Alerts: {log_stats['alert_count']} | "
                f"Queue: {src_stats.get('queue_size', 0)}"
            )

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        stop_event.set()
        data_source.stop()
        logger.info("Backend stopped.")


if __name__ == "__main__":
    main()
