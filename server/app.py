from flask import Flask, request, jsonify
import jwt
import datetime
import requests
import logging
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "super_secret")
AI_SERVER = "http://127.0.0.1:5001/detect"

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("server")

devices = {}
TOKEN_TTL = 10

ANOMALY_THRESHOLD = 3   # ✅ NEW


def decode_token(header):
    if not header or not header.startswith("Bearer "):
        return None, "Missing token"

    try:
        token = header.split()[1]
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["device_id"], None
    except jwt.ExpiredSignatureError:
        return None, "Expired token"
    except jwt.InvalidTokenError:
        return None, "Invalid token"


def query_ai(metrics):
    try:
        res = requests.post(AI_SERVER, json=metrics, timeout=3)
        res.raise_for_status()
        return res.json().get("status", "normal")
    except Exception as e:
        log.error(f"[AI ERROR] {e}")
        return "normal"


@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}

    device_id = data.get("device_id")
    secret = data.get("secret")

    if not device_id or not secret:
        return jsonify({"error": "Invalid request"}), 400

    # ✅ Add anomaly counter
    devices[device_id] = {
        "secret": secret,
        "status": "active",
        "anomaly_count": 0
    }

    log.info(f"Device registered: {device_id}")
    return jsonify({"message": "Registered"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}

    device_id = data.get("device_id")
    secret = data.get("secret")

    device = devices.get(device_id)

    if not device or device["secret"] != secret:
        return jsonify({"error": "Invalid credentials"}), 401

    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_TTL)

    token = jwt.encode(
        {"device_id": device_id, "exp": exp},
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({"token": token})


@app.route("/data", methods=["POST"])
def data():
    device_id, err = decode_token(request.headers.get("Authorization"))
    if err:
        return jsonify({"error": err}), 401

    device = devices.get(device_id)
    if not device:
        return jsonify({"error": "Not registered"}), 404

    if device["status"] == "blocked":
        return jsonify({"error": "Blocked"}), 403

    payload = request.json or {}

    required = ["request_rate", "packet_size", "cpu_usage", "connection_time"]

    if any(k not in payload for k in required):
        return jsonify({"error": "Missing fields"}), 400

    metrics = {k: payload[k] for k in required}

    result = query_ai(metrics)

    # ✅ Improved anomaly handling
    if result == "anomaly":
        device["anomaly_count"] += 1

        log.warning(f"{device_id} anomaly ({device['anomaly_count']}/{ANOMALY_THRESHOLD})")

        if device["anomaly_count"] >= ANOMALY_THRESHOLD:
            device["status"] = "blocked"
            log.error(f"{device_id} BLOCKED after repeated anomalies")

            return jsonify({
                "message": "Blocked after repeated anomalies"
            }), 403

        return jsonify({
            "message": f"Anomaly detected ({device['anomaly_count']}/{ANOMALY_THRESHOLD})"
        }), 200

    # ✅ Reset on normal behavior
    device["anomaly_count"] = 0

    return jsonify({"message": "OK"})


if __name__ == "__main__":
    app.run(port=5000)

@app.route("/health")
def health():
    return {"status": "ok"}