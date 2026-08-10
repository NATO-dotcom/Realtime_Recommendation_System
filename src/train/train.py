import mlflow
import pandas as pd
import pickle
from surprise import Dataset, SVD, accuracy, Reader
from surprise.model_selection import train_test_split

# 1. Connect to your running Docker MLflow server

mlflow.set_tracking_uri("http://localhost:5001")

# 2. Set the experiment (Docker handles the artifact locations automatically now!)

experiment_name = "recsys-svd-experiment-v3"
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

        # Save the file locally first
        model_path = "svd_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(algo, f)
        
        # Tell MLflow to push it to your artifacts folder!
        mlflow.log_artifact(model_path, artifact_path="models")
        print(f"Run completed! Validation RMSE logged: {rmse:.4f}")
                
if __name__ == "__main__":
    train_model()