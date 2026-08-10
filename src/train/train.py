import mlflow
import pandas as pd
import pickle
from surprise import Dataset, SVD, accuracy, Reader
from surprise.model_selection import train_test_split

# 1. Connect to your running Docker MLflow server
mlflow.set_tracking_uri("http://localhost:5000")

# 2. Tell MLflow exactly where to save local artifacts for this experiment
# Ensure the path is relative to the root of your project
import os
artifact_location = f"file://{os.path.abspath('infrastructure/local_artifacts')}"

# 3. Create or set the experiment with the specific artifact location
experiment_name = "recsys-svd-experiment"
try:
    mlflow.create_experiment(experiment_name, artifact_location=artifact_location)
except mlflow.exceptions.RestException:
    pass # Experiment already exists

mlflow.set_experiment(experiment_name)

def train_model():

    print("Loading dataset from data/ratings.csv...")
    df = pd.read_csv("data/ratings.csv")
    
    # Tell surprise the rating scale is 1 to 5
    reader = Reader(rating_scale=(1, 5))
    # Load directly from our pandas dataframe
    data = Dataset.load_from_df(df[['user_id', 'item_id', 'rating']], reader)
    
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

    # Define hyperparameter grid
    params = {
        "n_factors": 50,
        "n_epochs": 20,
        "lr_all": 0.005,
        "reg_all": 0.02
    }

    print("Starting MLflow run...")
    with mlflow.start_run():
        mlflow.log_params(params)

        algo = SVD(**params)
        algo.fit(trainset)

        predictions = algo.test(testset)
        rmse = accuracy.rmse(predictions, verbose=False)

        mlflow.log_metric("rmse", rmse)

        model_path = "svd_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(algo, f)
        
        # mlflow.log_artifact(model_path, artifact_path="models")
        print(f"Run completed! Validation RMSE logged: {rmse:.4f}")
        
if __name__ == "__main__":
    train_model()