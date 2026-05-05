import os
import queue
import subprocess
import sys
import threading
import time
import requests
import customtkinter as ctk
from tkinter import messagebox, ttk

import auth
import splash

# --- CONFIGURATION ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    PYTHON_EXE = "pythonw" if sys.platform == "win32" else "python"
else:
    PYTHON_EXE = sys.executable

try:
    from device_simulator import DeviceSimulator
except ImportError:
    class DeviceSimulator: 
        def __init__(self, **kwargs): self.running = False
        def start(self): self.running = True
        def stop(self): self.running = False
        def set_attack_mode(self, val): pass

class SentinelGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SENTINEL :: IoT Zero-Trust Control Plane")
        self.geometry("1250x900")
        self.configure(fg_color="#0f0f13")

        # Security Manager
        self.auth_manager = auth.AuthManager()
        self.current_user = None

        # States
        self.ai_running = False
        self.zt_running = False
        self.log_queue = queue.Queue()
        self.processes = {}
        self.status_indicators = {}
        
        # Simulator
        self.simulator = DeviceSimulator(log_callback=self.enqueue_log)

        self.setup_styles()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Main container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # Start with Premium Splash
        splash.show_splash(self.container, self.show_login)

    def show_login(self):
        self.login_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.login_frame.pack(fill="both", expand=True)
        
        # Centered Card for Login
        login_box = ctk.CTkFrame(
            self.login_frame, 
            width=400, height=450, 
            corner_radius=15, 
            fg_color="#18181e", 
            border_width=1, 
            border_color="#00e5ff"
        )
        login_box.place(relx=0.5, rely=0.5, anchor="center")
        login_box.grid_propagate(False)
        
        ctk.CTkLabel(login_box, text="ADMIN LOGIN", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00e5ff").pack(pady=(40, 30))
        
        self.username_entry = ctk.CTkEntry(login_box, placeholder_text="Username", width=300, height=45)
        self.username_entry.pack(pady=(0, 20))
        
        self.password_entry = ctk.CTkEntry(login_box, placeholder_text="Password", show="*", width=300, height=45)
        self.password_entry.pack(pady=(0, 20))
        
        login_btn = ctk.CTkButton(
            login_box, text="AUTHENTICATE", width=300, height=45, 
            font=ctk.CTkFont(weight="bold"), 
            fg_color="#006b7a", hover_color="#00a8c2", 
            command=self.check_login
        )
        login_btn.pack(pady=(10, 20))

        # Reset Password Button
        reset_btn = ctk.CTkButton(
            login_box, text="Forgot Password?", fg_color="transparent", 
            text_color="#888888", hover_color="#222222", 
            command=self.show_reset_password
        )
        reset_btn.pack()

    def check_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        success, msg = self.auth_manager.authenticate(username, password)
        if success:
            self.current_user = username
            self.container.destroy()
            self.build_ui()
            self.after(200, self.flush_logs)
            self.after(1500, self.refresh_health_status)
        else:
            messagebox.showerror("Access Denied", msg)

    def show_reset_password(self):
        username = self.username_entry.get()
        if not username:
            messagebox.showerror("Error", "Please enter your username first.")
            return
            
        sec_q = self.auth_manager.get_security_question(username)
        if not sec_q:
            messagebox.showerror("Error", "User not found or no security question set.")
            return

        reset_win = ctk.CTkToplevel(self)
        reset_win.title("Reset Password")
        reset_win.geometry("400x350")
        reset_win.transient(self)
        reset_win.grab_set()

        ctk.CTkLabel(reset_win, text=f"Security Question:\n{sec_q}", font=ctk.CTkFont(weight="bold")).pack(pady=20)
        
        ans_entry = ctk.CTkEntry(reset_win, placeholder_text="Answer", width=250)
        ans_entry.pack(pady=10)
        
        new_pass_entry = ctk.CTkEntry(reset_win, placeholder_text="New Password", show="*", width=250)
        new_pass_entry.pack(pady=10)
        
        def do_reset():
            ans = ans_entry.get()
            new_pass = new_pass_entry.get()
            success, msg = self.auth_manager.reset_password(username, ans, new_pass)
            if success:
                messagebox.showinfo("Success", "Password reset successful.")
                reset_win.destroy()
            else:
                messagebox.showerror("Failed", msg)

        ctk.CTkButton(reset_win, text="Reset Password", command=do_reset).pack(pady=20)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        
        # Standard Treeview
        style.configure("Treeview", background="#1e1e24", foreground="#ffffff", fieldbackground="#1e1e24", rowheight=35, borderwidth=0, font=("Segoe UI", 10))
        style.map("Treeview", background=[('selected', '#006b7a')])
        style.configure("Treeview.Heading", background="#2a2a35", foreground="#00e5ff", relief="flat", font=("Segoe UI", 11, "bold"))
        
        # Telemetry Log Treeview (Monospace)
        style.configure("Log.Treeview", background="#0a0a0c", foreground="#00e5ff", fieldbackground="#0a0a0c", rowheight=25, font=("Consolas", 10))
        style.map("Log.Treeview", background=[('selected', '#113344')])

    def build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (Darker Card) ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#18181e")
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # Branding
        ctk.CTkLabel(self.sidebar, text="SENTINEL", font=ctk.CTkFont(size=26, weight="bold"), text_color="#00e5ff").pack(pady=(30, 0))
        ctk.CTkLabel(self.sidebar, text="CONTROL PLANE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#aaaaaa").pack(pady=(0, 30))

        # Core Services Panel
        services_frame = ctk.CTkFrame(self.sidebar, fg_color="#22222a", corner_radius=10)
        services_frame.pack(padx=15, pady=10, fill="x")
        ctk.CTkLabel(services_frame, text="CORE SERVICES", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=10)

        # AI Server Status & Button
        self.ai_status_label = ctk.CTkLabel(services_frame, text="🔴 Stopped", text_color="#ff4444", font=ctk.CTkFont(weight="bold"))
        self.ai_status_label.pack()
        self.btn_ai = ctk.CTkButton(services_frame, text="START AI SERVER", fg_color="#006b7a", hover_color="#00a8c2", command=self.toggle_ai_server, font=ctk.CTkFont(weight="bold"))
        self.btn_ai.pack(padx=15, pady=(5, 15))

        # ZT Gateway Status & Button
        self.zt_status_label = ctk.CTkLabel(services_frame, text="🔴 Stopped", text_color="#ff4444", font=ctk.CTkFont(weight="bold"))
        self.zt_status_label.pack()
        self.btn_zt = ctk.CTkButton(services_frame, text="START ZT GATEWAY", fg_color="#006b7a", hover_color="#00a8c2", command=self.toggle_zt_server, font=ctk.CTkFont(weight="bold"))
        self.btn_zt.pack(padx=15, pady=(5, 15))

        # Simulator Panel
        sim_frame = ctk.CTkFrame(self.sidebar, fg_color="#22222a", corner_radius=10)
        sim_frame.pack(padx=15, pady=10, fill="x")
        ctk.CTkLabel(sim_frame, text="TRAFFIC SIMULATOR", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=10)
        
        self.sim_btn = ctk.CTkButton(sim_frame, text="ENABLE SIMULATOR", fg_color="#444455", hover_color="#555566", command=self.toggle_simulator, font=ctk.CTkFont(weight="bold"))
        self.sim_btn.pack(padx=15, pady=5)
        
        self.mode_switch = ctk.CTkSegmentedButton(sim_frame, values=["Normal", "Attack"], command=self.set_traffic_mode, selected_color="#006b7a", selected_hover_color="#00a8c2")
        self.mode_switch.set("Normal")
        self.mode_switch.pack(padx=15, pady=(5, 15))

        # Admin Panel Button
        admin_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        admin_frame.pack(side="bottom", pady=20, fill="x")
        ctk.CTkButton(admin_frame, text="Admin Settings ⚙️", fg_color="transparent", border_width=1, border_color="#555566", hover_color="#22222a", command=self.open_admin_panel).pack(padx=20)

        # --- MAIN PANEL ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(3, weight=1)

        # 1. Device Control Card
        ctk.CTkLabel(self.main_area, text="🛡️ DEVICE ACCESS CONTROL", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        device_card = ctk.CTkFrame(self.main_area, corner_radius=15, fg_color="#18181e")
        device_card.grid(row=1, column=0, sticky="nsew", pady=(0, 25))
        
        self.device_tree = ttk.Treeview(device_card, columns=("ID", "Type", "Status", "Risk"), show="headings", height=5)
        self.device_tree.heading("ID", text="DEVICE ID")
        self.device_tree.heading("Type", text="CATEGORY")
        self.device_tree.heading("Status", text="ACCESS STATUS")
        self.device_tree.heading("Risk", text="RISK LEVEL")
        self.device_tree.pack(side="left", fill="both", expand=True, padx=15, pady=15)

        # Action Buttons for Devices
        btn_frame = ctk.CTkFrame(device_card, width=120, fg_color="transparent")
        btn_frame.pack(side="right", fill="y", padx=15, pady=15)
        
        ctk.CTkButton(btn_frame, text="ALLOW", fg_color="#1e8449", hover_color="#27ae60", width=100, font=ctk.CTkFont(weight="bold"), command=lambda: self.manage_device("ALLOWED")).pack(pady=5)
        ctk.CTkButton(btn_frame, text="BLOCK", fg_color="#c0392b", hover_color="#e74c3c", width=100, font=ctk.CTkFont(weight="bold"), command=lambda: self.manage_device("BLOCKED")).pack(pady=5)

        # 2. Tabular Activity Logs Card
        ctk.CTkLabel(self.main_area, text="📜 SYSTEM TELEMETRY (REAL-TIME)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=2, column=0, sticky="w", pady=(0, 10))
        
        log_card = ctk.CTkFrame(self.main_area, corner_radius=15, fg_color="#18181e")
        log_card.grid(row=3, column=0, sticky="nsew")
        
        self.log_tree = ttk.Treeview(log_card, style="Log.Treeview", columns=("Time", "Source", "Message"), show="headings")
        self.log_tree.heading("Time", text="TIMESTAMP")
        self.log_tree.heading("Source", text="COMPONENT")
        self.log_tree.heading("Message", text="EVENT DETAILS")
        self.log_tree.column("Time", width=120, anchor="center")
        self.log_tree.column("Source", width=150, anchor="center")
        self.log_tree.column("Message", width=600, anchor="w")
        self.log_tree.pack(fill="both", expand=True, padx=15, pady=15)

        # Pre-populate dummy devices
        self.device_tree.insert("", "end", values=("device_camera_01", "IP Camera", "ALLOWED", "LOW"))
        self.device_tree.insert("", "end", values=("device_thermo_02", "Smart HVAC", "ALLOWED", "LOW"))
        self.enqueue_log(f"SYSTEM: Initialized workspace for Admin: {self.current_user}")

    # --- ADMIN PANEL ---
    def open_admin_panel(self):
        admin_win = ctk.CTkToplevel(self)
        admin_win.title("Admin Settings")
        admin_win.geometry("450x450")
        admin_win.transient(self)
        admin_win.grab_set()

        ctk.CTkLabel(admin_win, text="ADD NEW ADMIN", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        user_entry = ctk.CTkEntry(admin_win, placeholder_text="New Username", width=250)
        user_entry.pack(pady=10)
        pass_entry = ctk.CTkEntry(admin_win, placeholder_text="New Password", show="*", width=250)
        pass_entry.pack(pady=10)
        sec_q_entry = ctk.CTkEntry(admin_win, placeholder_text="Security Question (e.g. Pet name?)", width=250)
        sec_q_entry.pack(pady=10)
        sec_a_entry = ctk.CTkEntry(admin_win, placeholder_text="Security Answer", show="*", width=250)
        sec_a_entry.pack(pady=10)
        
        curr_pass_entry = ctk.CTkEntry(admin_win, placeholder_text="Your Current Password", show="*", width=250, border_color="#00e5ff")
        curr_pass_entry.pack(pady=20)

        def do_add_admin():
            success, msg = self.auth_manager.add_admin(
                self.current_user, curr_pass_entry.get(),
                user_entry.get(), pass_entry.get(),
                sec_q_entry.get(), sec_a_entry.get()
            )
            if success:
                messagebox.showinfo("Success", msg)
                admin_win.destroy()
            else:
                messagebox.showerror("Failed", msg)

        ctk.CTkButton(admin_win, text="Create Admin", fg_color="#006b7a", hover_color="#00a8c2", command=do_add_admin).pack()

    # --- LOGIC ---
    def toggle_ai_server(self):
        if not self.ai_running:
            self.launch_process("ai_server", "ai/ai_server.py")
        else:
            self.stop_process("ai_server")

    def toggle_zt_server(self):
        if not self.zt_running:
            self.launch_process("zero_trust_server", "zero_trust_server.py")
        else:
            self.stop_process("zero_trust_server")

    def manage_device(self, action):
        selected = self.device_tree.selection()
        if not selected:
            messagebox.showinfo("Select Device", "Please select a device from the table first.")
            return
        for item in selected:
            values = list(self.device_tree.item(item, "values"))
            values[2] = action
            self.device_tree.item(item, values=values)
            self.enqueue_log(f"MANUAL OVERRIDE: {values[0]} set to {action}")

    def enqueue_log(self, msg):
        source = "SYSTEM"
        clean_msg = msg
        if ":" in msg:
            source, clean_msg = msg.split(":", 1)
        self.log_queue.put((time.strftime('%H:%M:%S'), source.strip(), clean_msg.strip()))

    def flush_logs(self):
        while not self.log_queue.empty():
            entry = self.log_queue.get()
            self.log_tree.insert("", 0, values=entry) 
        self.after(200, self.flush_logs)

    # --- PROCESS HELPERS ---
    def launch_process(self, key, script):
        script_path = os.path.join(BASE_DIR, script)
        if not os.path.exists(script_path):
            self.enqueue_log(f"ERROR: Cannot find {script_path}")
            return
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
            self.sim_btn.configure(text="ENABLE SIMULATOR", fg_color="#444455")
            self.enqueue_log("SIMULATOR: Stopped")
        else:
            self.simulator.start()
            self.sim_btn.configure(text="STOP SIMULATOR", fg_color="#c0392b")
            self.enqueue_log("SIMULATOR: Started")

    def set_traffic_mode(self, value):
        self.simulator.set_attack_mode(value == "Attack")

    def is_up(self, url):
        try: return requests.get(url, timeout=0.5).ok
        except: return False

    def refresh_health_status(self):
        ai_up = self.is_up("http://127.0.0.1:5001/health")
        zt_up = self.is_up("http://127.0.0.1:5000/health")
        
        if ai_up != self.ai_running:
            self.ai_running = ai_up
            self.btn_ai.configure(text="STOP AI SERVER" if ai_up else "START AI SERVER", fg_color="#c0392b" if ai_up else "#006b7a")
            self.ai_status_label.configure(text="🟢 Running" if ai_up else "🔴 Stopped", text_color="#2ecc71" if ai_up else "#ff4444")
        
        if zt_up != self.zt_running:
            self.zt_running = zt_up
            self.btn_zt.configure(text="STOP ZT GATEWAY" if zt_up else "START ZT GATEWAY", fg_color="#c0392b" if zt_up else "#006b7a")
            self.zt_status_label.configure(text="🟢 Running" if zt_up else "🔴 Stopped", text_color="#2ecc71" if zt_up else "#ff4444")

        self.after(2000, self.refresh_health_status)

    def on_close(self):
        self.simulator.stop()
        for p in self.processes.values(): p.terminate()
        self.destroy()

if __name__ == "__main__":
    app = SentinelGUI()
    app.mainloop()