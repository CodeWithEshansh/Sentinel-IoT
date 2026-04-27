import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

# Load dataset
df = pd.read_csv("iot_device_data.csv")

# Keep only normal-like data (VERY IMPORTANT)
df_clean = df[
    (df["request_rate"] >= 1) & (df["request_rate"] <= 15) &
    (df["packet_size"] >= 80) & (df["packet_size"] <= 400) &
    (df["cpu_usage"] >= 10) & (df["cpu_usage"] <= 65) &
    (df["connection_time"] >= 0.5) & (df["connection_time"] <= 5)
]

print("Original size:", len(df))
print("Cleaned size:", len(df_clean))

# Features
features = ["request_rate", "packet_size", "cpu_usage", "connection_time"]
X = df_clean[features]

# Scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train model
model = IsolationForest(
    contamination=0.2,
    random_state=42
)
model.fit(X_scaled)

# Save new model
joblib.dump(model, "anomaly_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("✅ New model trained and saved!")