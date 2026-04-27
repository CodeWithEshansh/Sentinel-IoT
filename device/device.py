import requests
import time
import random
import threading
from dataclasses import dataclass

SERVER_URL = "http://127.0.0.1:5000"
SECRET_KEY = "abc123"

attack_mode_global = False
lock = threading.Lock()
stop_simulation = False


@dataclass
class DeviceProfile:
    device_id: str
    device_type: str
    normal_request_rate: tuple
    normal_packet_size: tuple
    normal_cpu_usage: tuple
    normal_connection_time: tuple
    attack_request_rate: tuple
    attack_packet_size: tuple
    attack_cpu_usage: tuple
    attack_connection_time: tuple
    poll_interval: float = 5.0


DEVICE_PROFILES = [
    DeviceProfile("device_thermostat", "Thermostat",
                  (1, 4), (80, 130), (10, 25), (0.5, 2),
                  (25, 50), (250, 500), (75, 90), (8, 18)),

    DeviceProfile("device_industrial", "Industrial",
                  (5, 12), (150, 250), (35, 55), (2, 5),
                  (60, 100), (500, 900), (88, 99), (15, 30)),

    DeviceProfile("device_camera", "Camera",
                  (8, 15), (200, 400), (40, 65), (1, 3),
                  (80, 150), (600, 1200), (90, 99), (12, 25)),
]


def rng(r):
    return round(random.uniform(*r), 2)


def register_and_login(profile):
    try:
        requests.post(f"{SERVER_URL}/register",
                      json={"device_id": profile.device_id, "secret": SECRET_KEY})

        res = requests.post(f"{SERVER_URL}/login",
                            json={"device_id": profile.device_id, "secret": SECRET_KEY})

        return res.json().get("token")
    except:
        return None


def run_device(profile):
    global stop_simulation

    token = register_and_login(profile)
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    while not stop_simulation:
        with lock:
            attack = attack_mode_global

        mode = "attack" if attack else "normal"

        payload = {
            "device_id": profile.device_id,
            "request_rate": rng(getattr(profile, f"{mode}_request_rate")),
            "packet_size": rng(getattr(profile, f"{mode}_packet_size")),
            "cpu_usage": rng(getattr(profile, f"{mode}_cpu_usage")),
            "connection_time": rng(getattr(profile, f"{mode}_connection_time")),
        }

        try:
            res = requests.post(f"{SERVER_URL}/data", json=payload, headers=headers)
            print(profile.device_id, res.text)
        except Exception as e:
            print(profile.device_id, "ERROR:", e)

        time.sleep(profile.poll_interval)


# ---------- GUI CONTROL FUNCTIONS ----------

def start_simulation():
    global stop_simulation
    stop_simulation = False

    for profile in DEVICE_PROFILES:
        threading.Thread(target=run_device, args=(profile,), daemon=True).start()


def stop_all():
    global stop_simulation
    stop_simulation = True


def set_attack_mode(value: bool):
    global attack_mode_global
    with lock:
        attack_mode_global = value