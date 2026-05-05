import os
import json
import hashlib
import base64
import time
from datetime import datetime

import sys

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(base_dir, ".secure_config.json")
AUDIT_FILE = os.path.join(base_dir, ".audit_log.txt")

class AuthManager:
    def __init__(self):
        self.failed_attempts = {}
        self.lockout_time = {}
        self.MAX_ATTEMPTS = 3
        self.LOCKOUT_DURATION = 60 # 60 seconds lockout
        self._ensure_config()
        self._config = self._load_config()

    def _hash_password(self, password, salt):
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

    def _ensure_config(self):
        if not os.path.exists(CONFIG_FILE):
            salt = os.urandom(16).hex()
            default_config = {
                "admins": {
                    "admin": {
                        "salt": salt,
                        "hash": self._hash_password("admin", salt),
                        "sec_q": "What is the default role?",
                        "sec_a_hash": self._hash_password("admin", salt)
                    }
                }
            }
            self._save_config(default_config)
            self.log_audit("SYSTEM", "Created default admin configuration.")

    def _load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                encoded = f.read()
                decoded = base64.b64decode(encoded).decode('utf-8')
                return json.loads(decoded)
        except Exception as e:
            self.log_audit("SYSTEM", f"Failed to load config: {str(e)}")
            return {"admins": {}}

    def _save_config(self, config_data):
        try:
            encoded = base64.b64encode(json.dumps(config_data).encode('utf-8')).decode('utf-8')
            with open(CONFIG_FILE, 'w') as f:
                f.write(encoded)
            self._config = config_data
        except Exception as e:
            self.log_audit("SYSTEM", f"Failed to save config: {str(e)}")

    def is_locked_out(self, username):
        if username in self.lockout_time:
            if time.time() < self.lockout_time[username]:
                return True
            else:
                del self.lockout_time[username]
                self.failed_attempts[username] = 0
        return False

    def authenticate(self, username, password):
        if self.is_locked_out(username):
            self.log_audit(username, "Failed login attempt (Account locked).")
            return False, "Account is temporarily locked due to multiple failed attempts."

        admins = self._config.get("admins", {})
        if username not in admins:
            self.log_audit(username, "Failed login attempt (Unknown user).")
            self._increment_failure(username)
            return False, "Invalid credentials."

        user_data = admins[username]
        calc_hash = self._hash_password(password, user_data["salt"])

        if calc_hash == user_data["hash"]:
            self.failed_attempts[username] = 0
            self.log_audit(username, "Successful login.")
            return True, "Success"
        else:
            self._increment_failure(username)
            self.log_audit(username, "Failed login attempt (Incorrect password).")
            if self.is_locked_out(username):
                return False, "Account locked out due to too many failed attempts."
            return False, "Invalid credentials."

    def _increment_failure(self, username):
        self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
        if self.failed_attempts[username] >= self.MAX_ATTEMPTS:
            self.lockout_time[username] = time.time() + self.LOCKOUT_DURATION

    def add_admin(self, current_user, current_password, new_username, new_password, sec_q, sec_a):
        success, _ = self.authenticate(current_user, current_password)
        if not success:
            return False, "Current admin authentication failed."
        
        if new_username in self._config["admins"]:
            return False, "Admin already exists."

        salt = os.urandom(16).hex()
        self._config["admins"][new_username] = {
            "salt": salt,
            "hash": self._hash_password(new_password, salt),
            "sec_q": sec_q,
            "sec_a_hash": self._hash_password(sec_a.lower().strip(), salt)
        }
        self._save_config(self._config)
        self.log_audit(current_user, f"Added new admin: {new_username}.")
        return True, "Admin successfully added."

    def get_security_question(self, username):
        if username in self._config.get("admins", {}):
            return self._config["admins"][username].get("sec_q", "No security question set.")
        return None

    def reset_password(self, username, sec_a, new_password):
        admins = self._config.get("admins", {})
        if username not in admins:
            return False, "User not found."

        user_data = admins[username]
        calc_sec_hash = self._hash_password(sec_a.lower().strip(), user_data["salt"])

        if calc_sec_hash == user_data.get("sec_a_hash"):
            user_data["salt"] = os.urandom(16).hex()
            user_data["hash"] = self._hash_password(new_password, user_data["salt"])
            user_data["sec_a_hash"] = self._hash_password(sec_a.lower().strip(), user_data["salt"])
            
            self._save_config(self._config)
            self.log_audit(username, "Password reset successfully via security question.")
            self.failed_attempts[username] = 0
            if username in self.lockout_time: del self.lockout_time[username]
            return True, "Password reset successfully."
        else:
            self.log_audit(username, "Failed password reset attempt (wrong security answer).")
            self._increment_failure(username)
            return False, "Incorrect security answer."

    def log_audit(self, user, action):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] User: {user} | Action: {action}\n"
        try:
            with open(AUDIT_FILE, "a") as f:
                f.write(log_entry)
        except:
            pass
