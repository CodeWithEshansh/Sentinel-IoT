import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

print("Loading dataset...")

# load dataset
df = pd.read_csv("iot_device_data.csv")

# select features
X = df[['request_rate','packet_size','cpu_usage','connection_time']]

print("Normalizing data...")

# normalize data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("Training Isolation Forest...")

# train model
model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)

model.fit(X_scaled)

# save model
joblib.dump(model,"anomaly_model.pkl")
joblib.dump(scaler,"scaler.pkl")

print("Model trained and saved successfully!")