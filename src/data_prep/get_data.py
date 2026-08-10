import pandas as pd
import urllib.request
import zipfile
import os
import shutil

def fetch_data():
    print("Downloading MovieLens 100k dataset...")
    url = "http://files.grouplens.org/datasets/movielens/ml-100k.zip"
    urllib.request.urlretrieve(url, "data/ml-100k.zip")

    print("Extracting data...")
    with zipfile.ZipFile("data/ml-100k.zip", 'r') as zip_ref:
        zip_ref.extractall("data/")

    print("Converting to a clean CSV...")
    # The raw file is tab-separated: user_id | item_id | rating | timestamp
    raw_data_path = "data/ml-100k/u.data"
    df = pd.read_csv(raw_data_path, sep='\t', names=['user_id', 'item_id', 'rating', 'timestamp'])
    
    # Save as a standard CSV
    df.to_csv("data/ratings.csv", index=False)

    # Clean up the downloaded zip and extracted folder to keep things tidy
    os.remove("data/ml-100k.zip")
    shutil.rmtree("data/ml-100k")
    
    print("Success! Data saved to data/ratings.csv")

if __name__ == "__main__":
    fetch_data()