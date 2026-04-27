import os
import queue
import subprocess
import sys
import threading
import time
import requests
import customtkinter as ctk
from tkinter import messagebox, ttk

# --- CONFIGURATION ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable

# Try to import simulator, fallback for testing if file missing
try:
    from device_simulator import DeviceSimulator
except ImportError:
    class DeviceSimulator: # Mock for structure
        def __init__(self, **kwargs): self.running = False
        def start(self): self.running = True
        def stop(self): self.running = False
        def set_attack_mode(self, val): pass

class SentinelGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SENTINEL :: IoT Zero-Trust Control Plane")
        self.geometry("1200x850")

        # States
        self.ai_running = False
        self.zt_running = False
        self.log_queue = queue.Queue()
        self.processes = {}
        self.status_indicators = {}
        
        # Simulator
        self.simulator = DeviceSimulator(log_callback=self.enqueue_log)

        self.setup_styles()
        self.build_ui()

        # Loops
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(200, self.flush_logs)
        self.after(1500, self.refresh_health_status)

    def setup_styles(self):
        """Customizing the Tabular Treeview for Dark Mode"""
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#1a1a1a",
                        foreground="white",
                        fieldbackground="#1a1a1a",
                        rowheight=30,
                        borderwidth=0,
                        font=("Segoe UI", 10))
        style.map("Treeview", background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading",
                        background="#2c3e50",
                        foreground="white",
                        relief="flat",
                        font=("Segoe UI", 11, "bold"))

    def build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="SENTINEL", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 0))
        ctk.CTkLabel(self.sidebar, text="CONTROL PLANE", font=ctk.CTkFont(size=10)).pack(pady=(0, 20))

        # TOGGLE BUTTONS
        self.btn_ai = ctk.CTkButton(self.sidebar, text="START AI SERVER", fg_color="#27ae60", 
                                   command=self.toggle_ai_server)
        self.btn_ai.pack(padx=20, pady=10)

        self.btn_zt = ctk.CTkButton(self.sidebar, text="START ZT GATEWAY", fg_color="#27ae60", 
                                   command=self.toggle_zt_server)
        self.btn_zt.pack(padx=20, pady=10)

        # Simulator Controls
        ctk.CTkLabel(self.sidebar, text="TRAFFIC SIMULATOR", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(30, 5))
        self.sim_btn = ctk.CTkButton(self.sidebar, text="ENABLE SIMULATOR", command=self.toggle_simulator)
        self.sim_btn.pack(padx=20, pady=10)
        
        self.mode_switch = ctk.CTkSegmentedButton(self.sidebar, values=["Normal", "Attack"], command=self.set_traffic_mode)
        self.mode_switch.set("Normal")
        self.mode_switch.pack(padx=20, pady=10)

        # --- MAIN PANEL ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)

        # 1. Device Control Table
        ctk.CTkLabel(self.main_area, text="🛡️ DEVICE ACCESS CONTROL", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        device_frame = ctk.CTkFrame(self.main_area)
        device_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        
        self.device_tree = ttk.Treeview(device_frame, columns=("ID", "Type", "Status", "Risk"), show="headings", height=6)
        self.device_tree.heading("ID", text="DEVICE ID")
        self.device_tree.heading("Type", text="CATEGORY")
        self.device_tree.heading("Status", text="ACCESS STATUS")
        self.device_tree.heading("Risk", text="RISK LEVEL")
        self.device_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Action Buttons for Devices
        btn_frame = ctk.CTkFrame(device_frame, width=150, fg_color="transparent")
        btn_frame.pack(side="right", fill="y", padx=10)
        
        ctk.CTkButton(btn_frame, text="ALLOW", fg_color="#2ecc71", width=100, command=lambda: self.manage_device("ALLOWED")).pack(pady=5)
        ctk.CTkButton(btn_frame, text="BLOCK", fg_color="#e74c3c", width=100, command=lambda: self.manage_device("BLOCKED")).pack(pady=5)

        # 2. Tabular Activity Logs
        ctk.CTkLabel(self.main_area, text="📜 SYSTEM TELEMETRY (REAL-TIME)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=2, column=0, sticky="w", pady=(0, 10))
        
        log_frame = ctk.CTkFrame(self.main_area)
        log_frame.grid(row=3, column=0, sticky="nsew")
        
        self.log_tree = ttk.Treeview(log_frame, columns=("Time", "Source", "Message"), show="headings", height=12)
        self.log_tree.heading("Time", text="TIMESTAMP")
        self.log_tree.heading("Source", text="COMPONENT")
        self.log_tree.heading("Message", text="EVENT DETAILS")
        self.log_tree.column("Time", width=100)
        self.log_tree.column("Source", width=150)
        self.log_tree.column("Message", width=600)
        self.log_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Pre-populate some dummy devices for the demo
        self.device_tree.insert("", "end", values=("device_camera_01", "IP Camera", "ALLOWED", "LOW"))
        self.device_tree.insert("", "end", values=("device_thermo_02", "Smart HVAC", "ALLOWED", "LOW"))

    # --- LOGIC ---
    def toggle_ai_server(self):
        if not self.ai_running:
            self.launch_process("ai_server", "ai/ai_server.py")
            self.btn_ai.configure(text="STOP AI SERVER", fg_color="#c0392b")
            self.ai_running = True
        else:
            self.stop_process("ai_server")
            self.btn_ai.configure(text="START AI SERVER", fg_color="#27ae60")
            self.ai_running = False

    def toggle_zt_server(self):
        if not self.zt_running:
            self.launch_process("zero_trust_server", "zero_trust_server.py")
            self.btn_zt.configure(text="STOP ZT GATEWAY", fg_color="#c0392b")
            self.zt_running = True
        else:
            self.stop_process("zero_trust_server")
            self.btn_zt.configure(text="START ZT GATEWAY", fg_color="#27ae60")
            self.zt_running = False

    def manage_device(self, action):
        selected = self.device_tree.selection()
        if not selected:
            messagebox.showinfo("Select Device", "Please select a device from the table first.")
            return
        
        for item in selected:
            values = list(self.device_tree.item(item, "values"))
            values[2] = action  # Update status column
            self.device_tree.item(item, values=values)
            self.enqueue_log(f"MANUAL OVERRIDE: {values[0]} set to {action}")

    def enqueue_log(self, msg):
        # Format: [Component] Message
        source = "SYSTEM"
        clean_msg = msg
        if ":" in msg:
            source, clean_msg = msg.split(":", 1)
        
        self.log_queue.put((time.strftime('%H:%M:%S'), source.strip(), clean_msg.strip()))

    def flush_logs(self):
        while not self.log_queue.empty():
            entry = self.log_queue.get()
            self.log_tree.insert("", 0, values=entry) # Insert at top
        self.after(200, self.flush_logs)

    # --- PROCESS HELPERS ---
    def launch_process(self, key, script):
        script_path = os.path.join(BASE_DIR, script)
        process = subprocess.Popen([PYTHON_EXE, script_path], cwd=BASE_DIR, 
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.processes[key] = process
        threading.Thread(target=self.stream_output, args=(key, process), daemon=True).start()

    def stop_process(self, key):
        if key in self.processes:
            self.processes[key].terminate()
            del self.processes[key]

    def stream_output(self, key, process):
        for line in iter(process.stdout.readline, ""):
            if line.strip(): self.enqueue_log(f"{key.upper()}: {line.strip()}")

    def toggle_simulator(self):
        if getattr(self.simulator, "running", False):
            self.simulator.stop()
            self.sim_btn.configure(text="ENABLE SIMULATOR", fg_color="#34495e")
        else:
            self.simulator.start()
            self.sim_btn.configure(text="STOP SIMULATOR", fg_color="#c0392b")

    def set_traffic_mode(self, value):
        self.simulator.set_attack_mode(value == "Attack")

    def is_up(self, url):
        try: return requests.get(url, timeout=0.5).ok
        except: return False

    def refresh_health_status(self):
        # Logic to sync UI if servers crash/stop externally
        ai_up = self.is_up("http://127.0.0.1:5001/health")
        zt_up = self.is_up("http://127.0.0.1:5000/health")
        
        # Auto-update toggle button visuals if status changes
        if ai_up != self.ai_running:
            self.ai_running = ai_up
            self.btn_ai.configure(text="STOP AI SERVER" if ai_up else "START AI SERVER", 
                                 fg_color="#c0392b" if ai_up else "#27ae60")
        
        if zt_up != self.zt_running:
            self.zt_running = zt_up
            self.btn_zt.configure(text="STOP ZT GATEWAY" if zt_up else "START ZT GATEWAY", 
                                 fg_color="#c0392b" if zt_up else "#27ae60")

        self.after(2000, self.refresh_health_status)

    def on_close(self):
        self.simulator.stop()
        for p in self.processes.values(): p.terminate()
        self.destroy()

if __name__ == "__main__":
    app = SentinelGUI()
    app.mainloop()