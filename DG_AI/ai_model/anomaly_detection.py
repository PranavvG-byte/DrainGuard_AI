"""
DrainGuard AI - Anomaly Detection (Real-time Inference)
Loads the trained Isolation Forest model and provides real-time anomaly prediction.
"""

import os
import time
import logging
import numpy as np
import pandas as pd
import joblib
from collections import deque


from config.settings import (
    MODEL_PATH,
    FEATURE_ROLLING_WINDOW,
    ANOMALY_COOLDOWN_SECONDS,
    WATER_BLOCKAGE_THRESHOLD,
    WATER_LEAKAGE_THRESHOLD,
    GAS_DANGER_THRESHOLD,
    GAS_WARNING_THRESHOLD,
    RISK_LEVELS,
)

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Real-time anomaly detection using trained Isolation Forest."""

    def __init__(self, model_path=MODEL_PATH):
        self._load_model(model_path)
        self._history = deque(maxlen=FEATURE_ROLLING_WINDOW * 2)
        self._last_alert_time = 0
        self._alert_count = 0

    def _load_model(self, model_path):
        """Load the trained model package."""
        if not os.path.exists(model_path):
            logger.warning(f"Model not found at {model_path}. Using rule-based fallback.")
            self._model = None
            self._scaler = None
            self._score_threshold = -0.1
            self._rolling_window = FEATURE_ROLLING_WINDOW
            self._feature_names = []
            return

        package = joblib.load(model_path)
        self._model = package["model"]
        self._scaler = package["scaler"]
        self._feature_names = package["feature_names"]
        self._rolling_window = package["rolling_window"]
        self._score_threshold = package.get("score_threshold", -0.1)
        logger.info(f"Model loaded from {model_path}")

    def predict(self, water_level: float, gas_level: float) -> dict:
        """
        Predict anomaly status for a sensor reading.
        
        Returns:
            dict with keys: is_anomaly, risk_score, risk_level, risk_type,
                           confidence, details
        """
        # Add to history
        self._history.append({"water_level_cm": water_level, "gas_level": gas_level})

        # Build features
        features = self._build_features(water_level, gas_level)

        # Model prediction
        if self._model is not None and len(self._history) >= 3:
            result = self._model_predict(features)
        else:
            result = self._rule_based_predict(water_level, gas_level)

        # Apply cooldown
        result["alert_suppressed"] = False
        if result["is_anomaly"]:
            now = time.time()
            if now - self._last_alert_time < ANOMALY_COOLDOWN_SECONDS:
                result["alert_suppressed"] = True
            else:
                self._last_alert_time = now
                self._alert_count += 1

        return result

    def _build_features(self, water_level, gas_level):
        """Build feature vector from current reading + history."""
        history_df = pd.DataFrame(list(self._history))

        window = min(len(history_df), self._rolling_window)

        features = {
            "water_level_cm": water_level,
            "gas_level": gas_level,
            "water_rolling_mean": history_df["water_level_cm"].tail(window).mean(),
            "water_rolling_std": history_df["water_level_cm"].tail(window).std() if window > 1 else 0,
            "gas_rolling_mean": history_df["gas_level"].tail(window).mean(),
            "gas_rolling_std": history_df["gas_level"].tail(window).std() if window > 1 else 0,
            "water_delta": water_level - history_df["water_level_cm"].iloc[-2] if len(history_df) > 1 else 0,
            "gas_delta": gas_level - history_df["gas_level"].iloc[-2] if len(history_df) > 1 else 0,
            "water_gas_ratio": water_level / max(gas_level, 1),
        }

        return features

    def _model_predict(self, features):
        """Use trained Isolation Forest for prediction."""
        # Create feature array in correct order
        X = np.array([[features[name] for name in self._feature_names]])
        X_scaled = self._scaler.transform(X)

        # Get anomaly score
        raw_score = self._model.decision_function(X_scaled)[0]
        prediction = self._model.predict(X_scaled)[0]  # 1 = normal, -1 = anomaly

        is_anomaly = prediction == -1

        # Convert score to 0-100 risk percentage
        # Lower decision_function scores = more anomalous
        risk_score = self._score_to_risk(raw_score)

        # Determine risk type
        risk_type = self._classify_risk_type(
            features["water_level_cm"],
            features["gas_level"],
            is_anomaly
        )

        # Determine risk level
        risk_level = self._get_risk_level(risk_score)

        return {
            "is_anomaly": is_anomaly,
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "risk_type": risk_type,
            "confidence": round(min(abs(raw_score) * 100, 99), 1),
            "raw_score": round(raw_score, 4),
            "details": self._generate_details(risk_type, features, risk_score),
        }

    def _rule_based_predict(self, water_level, gas_level):
        """Fallback rule-based prediction when model is not available."""
        risk_score = 0
        risk_type = "NORMAL"
        is_anomaly = False

        # Blockage check
        if water_level < WATER_BLOCKAGE_THRESHOLD:
            risk_score = max(risk_score, 70 + (WATER_BLOCKAGE_THRESHOLD - water_level) * 3)
            risk_type = "BLOCKAGE"
            is_anomaly = True

        # Leakage check
        if water_level > WATER_LEAKAGE_THRESHOLD:
            risk_score = max(risk_score, 60 + (water_level - WATER_LEAKAGE_THRESHOLD) * 0.5)
            risk_type = "LEAKAGE"
            is_anomaly = True

        # Gas hazard check
        if gas_level > GAS_DANGER_THRESHOLD:
            risk_score = max(risk_score, 80 + (gas_level - GAS_DANGER_THRESHOLD) * 0.02)
            risk_type = "GAS_HAZARD"
            is_anomaly = True
        elif gas_level > GAS_WARNING_THRESHOLD:
            risk_score = max(risk_score, 40 + (gas_level - GAS_WARNING_THRESHOLD) * 0.03)
            if risk_type == "NORMAL":
                risk_type = "GAS_HAZARD"
            is_anomaly = True

        # Flood risk (very low water level = very high water in drain)
        if water_level < 5.0 and gas_level > 800:
            risk_score = max(risk_score, 85)
            risk_type = "FLOOD_RISK"
            is_anomaly = True

        risk_score = min(risk_score, 100)
        risk_level = self._get_risk_level(risk_score)

        return {
            "is_anomaly": is_anomaly,
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "risk_type": risk_type,
            "confidence": 60.0,  # Lower confidence for rule-based
            "raw_score": 0,
            "details": self._generate_details(risk_type, {"water_level_cm": water_level, "gas_level": gas_level}, risk_score),
        }

    def _score_to_risk(self, raw_score):
        """Convert Isolation Forest decision function score to 0-100 risk percentage."""
        # decision_function: positive = normal, negative = anomaly
        # More negative = more anomalous
        if raw_score >= 0:
            # Normal range: 0-30% risk
            return max(0, 30 - raw_score * 100)
        else:
            # Anomalous range: 30-100% risk
            return min(100, 30 + abs(raw_score) * 200)

    def _classify_risk_type(self, water_level, gas_level, is_anomaly):
        """Determine the specific type of risk."""
        if not is_anomaly:
            return "NORMAL"

        if water_level < WATER_BLOCKAGE_THRESHOLD:
            if gas_level > GAS_WARNING_THRESHOLD:
                return "FLOOD_RISK"
            return "BLOCKAGE"
        elif water_level > WATER_LEAKAGE_THRESHOLD:
            return "LEAKAGE"
        elif gas_level > GAS_DANGER_THRESHOLD:
            return "GAS_HAZARD"
        elif gas_level > GAS_WARNING_THRESHOLD:
            return "GAS_HAZARD"
        else:
            return "BLOCKAGE"  # Default anomaly type

    def _get_risk_level(self, risk_score):
        """Map risk score to risk level label."""
        for level, config in RISK_LEVELS.items():
            if config["min_score"] <= risk_score < config["max_score"]:
                return level
        return "CRITICAL"

    def _generate_details(self, risk_type, features, risk_score):
        """Generate human-readable details about the detected condition."""
        water = features.get("water_level_cm", 0)
        gas = features.get("gas_level", 0)

        messages = {
            "NORMAL": f"System operating normally. Water: {water:.1f}cm, Gas: {gas}",
            "BLOCKAGE": f"Potential blockage detected. Water level critically low at {water:.1f}cm, "
                       f"indicating high water in drain pipe. Immediate inspection recommended.",
            "LEAKAGE": f"Possible leakage detected. Water level at {water:.1f}cm is abnormally high "
                      f"(low water in drain), suggesting pipe damage or unauthorized discharge.",
            "GAS_HAZARD": f"Hazardous gas concentration detected at {gas} ADC units. "
                         f"Ventilation required before personnel entry. Risk score: {risk_score:.0f}%.",
            "FLOOD_RISK": f"Flood risk condition. Water level at {water:.1f}cm with elevated gas at {gas}. "
                         f"Drain capacity may be exceeded. Alert municipal flood response team.",
        }

        return messages.get(risk_type, f"Anomalous condition detected. Water: {water:.1f}cm, Gas: {gas}")

    @property
    def stats(self):
        return {
            "model_loaded": self._model is not None,
            "history_length": len(self._history),
            "total_alerts": self._alert_count,
        }
