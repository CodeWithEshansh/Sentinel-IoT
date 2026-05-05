from flask import Flask, request, jsonify
import joblib
import numpy as np
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ai")

app = Flask(__name__)

FEATURES = ["request_rate", "packet_size", "cpu_usage", "connection_time"]

# Load model
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "anomaly_model.pkl")
scaler_path = os.path.join(BASE_DIR, "scaler.pkl")

model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

log.info("Model loaded ✓")


@app.route("/detect", methods=["POST"])
def detect():
    data = request.json or {}

    if any(f not in data for f in FEATURES):
        return jsonify({"error": "Missing fields"}), 400

    try:
        features = np.array([[float(data[f]) for f in FEATURES]])
        scaled = scaler.transform(features)

        prediction = model.predict(scaled)[0]   # ✅ fixed
    except Exception as e:
        log.error(f"Inference error: {e}")
        return jsonify({"error": "Inference failed"}), 500

    result = "anomaly" if prediction == -1 else "normal"

    return jsonify({"status": result})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5001)