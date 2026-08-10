import pandas as pd
from sqlalchemy import create_engine
import datetime

print("Loading data for comparison...")
df = pd.read_csv("data/ratings.csv")

reference_data = df.iloc[:50000]  
current_data = df.iloc[50000:60000] 

print("Calculating drift and business metrics...")

ref_mean = reference_data['rating'].mean()
curr_mean = current_data['rating'].mean()
drift_score = abs(ref_mean - curr_mean)

dataset_drift = bool(drift_score > 0.05)
share_of_drifted_columns = float(min(drift_score, 1.0))

# NEW METRICS:
avg_current_rating = float(curr_mean)
total_ratings = int(len(current_data))
unique_users = int(current_data['user_id'].nunique())

# Package ALL metrics into the dataframe
metrics_df = pd.DataFrame([{
    "timestamp": datetime.datetime.now(),
    "dataset_drift": dataset_drift,
    "share_of_drifted_columns": share_of_drifted_columns,
    "avg_current_rating": avg_current_rating,
    "total_ratings": total_ratings,
    "unique_users": unique_users
}])

print("Saving metrics to PostgreSQL...")
engine = create_engine("postgresql://mlflow_user:mlflow_password@localhost:5444/mlflow_db")
metrics_df.to_sql("evidently_metrics", engine, if_exists="replace", index=False)

print("✅ Rich metrics successfully logged to the database!")