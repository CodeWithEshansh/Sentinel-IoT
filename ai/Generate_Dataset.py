import pandas as pd
import numpy as np

np.random.seed(42)

n_samples = 1000

# Normal device behavior
request_rate = np.random.normal(loc=5, scale=1, size=n_samples)
packet_size = np.random.normal(loc=120, scale=20, size=n_samples)
cpu_usage = np.random.normal(loc=30, scale=5, size=n_samples)
connection_time = np.random.normal(loc=2, scale=0.5, size=n_samples)

data = pd.DataFrame({
    "request_rate": request_rate,
    "packet_size": packet_size,
    "cpu_usage": cpu_usage,
    "connection_time": connection_time
})

# Adding anomalies to the dataset
anomalies = pd.DataFrame({
    "request_rate": np.random.uniform(30,60,50),
    "packet_size": np.random.uniform(300,600,50),
    "cpu_usage": np.random.uniform(80,95,50),
    "connection_time": np.random.uniform(10,20,50)
})

dataset = pd.concat([data, anomalies])

dataset.to_csv("iot_device_data.csv", index=False)

print("Dataset Generated")