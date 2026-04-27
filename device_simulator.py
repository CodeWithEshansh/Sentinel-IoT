import threading
from device.device import start_simulation, stop_all, set_attack_mode


class DeviceSimulator:

    def __init__(self, log_callback=None):
        self.running = False
        self.log = log_callback or print

    def start(self):
        if self.running:
            self.log("Already running")
            return

        self.running = True
        threading.Thread(target=start_simulation, daemon=True).start()
        self.log("Simulator started")

    def stop(self):
        stop_all()
        self.running = False
        self.log("Simulator stopped")

    def set_attack_mode(self, attack):
        set_attack_mode(attack)
        mode = "ATTACK" if attack else "NORMAL"
        self.log(f"Mode: {mode}")