# 🛡️ Sentinel IoT  
### 🔐 Zero Trust Security Framework for IoT Environments

> A cloud-based IoT security system combining **Zero Trust Architecture + AI-powered anomaly detection** to protect smart devices in real time.

---

## ⚡ Highlights

✨ Real-time IoT monitoring  
🧠 AI-based anomaly detection (Isolation Forest)  
🔐 Zero Trust authentication using JWT  
🚫 Automated device blocking  
🖥️ Interactive GUI dashboard  

---

## 🧩 System Architecture
📡 Devices → 🛡️ Zero Trust Server → 🤖 AI Server → ⚖️ Decision Engine → 🚫 Block / ✅ Allow


---

## 🎯 Key Features

### 🔐 Zero Trust Security
- Device authentication using JWT tokens  
- Continuous verification (no implicit trust)  
- Token expiry + validation  

### 🤖 AI Anomaly Detection
- Isolation Forest model  
- Detects abnormal behavior patterns  
- Real-time classification: `normal` / `anomaly`  

### 📡 Multi-Device Simulation
- Simulates multiple IoT devices  
- Real-world traffic patterns  
- Supports attack scenarios  

### 🚨 Automated Response
- Tracks anomaly count  
- Blocks devices after threshold breach  

### 🖥️ GUI Dashboard
- Start/stop servers  
- Monitor system health  
- Toggle attack mode  
- View live logs  

---

## 🛠️ Tech Stack

| Layer | Technology |
|------|----------|
| Backend | Python, Flask |
| AI/ML | Scikit-learn (Isolation Forest) |
| GUI | Tkinter |
| Communication | REST APIs |
| Concepts | Networking, Cybersecurity, OOP |

---

## 📂 Project Structure
Sentinel-IoT/
│
├ ai/
│ ├ ai_server.py
│ ├ anomaly_model.pkl
│ └ scaler.pkl
│
├ device/
│ ├ init.py
│ └ device.py
│
├ server/
│ ├ init.py
│ └ app.py
│
├ gui.py
├ device_simulator.py
├ zero_trust_server.py

---

## ⚙️ Setup

### 🔽 Clone Repo
git clone https://github.com/your-username/sentinel-iot.git

cd sentinel-iot

---

### 📦 Install Dependencies
pip install flask requests numpy pandas scikit-learn


---

## ▶️ Run the Project

### 🎯 Recommended: GUI Mode
python gui.py


### 🔄 Execution Flow

1️⃣ Start AI Server  
2️⃣ Start Zero Trust Server  
3️⃣ Start Simulator  
4️⃣ Toggle Attack Mode (optional)  

---

### ⚙️ Manual Mode (Advanced)

#### Terminal 1 — AI Server
cd ai
python ai_server.py
#### Terminal 2 — Zero Trust Server

python zero_trust_server.py

#### Terminal 3 — Devices
python device/device.py

---

## 🧪 Demo Behavior

### ✅ Normal Mode
device_thermostat OK
device_camera OK

### 🚨 Attack Mode
device_camera anomaly (1/3)
device_camera anomaly (2/3)
device_camera BLOCKED


---

## 🔐 Security Concepts

- Zero Trust Architecture  
- Continuous Authentication  
- Behavioral Analysis  
- Automated Threat Mitigation  

---

## 📈 Future Enhancements

- 📊 Real-time graphs & dashboards  
- ☁️ Cloud deployment (AWS / GCP)  
- 🗄️ Database integration  
- 🧠 Deep learning models  

---

## 👨‍💻 Team

- Eshansh Verma  
- Kartik Chauhan  
- Aarush Mehrotra  
- Anant Pundir  

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!

---

## 📄 License

Academic Project – For educational purposes only
