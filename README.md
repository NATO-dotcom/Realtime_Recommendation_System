# 🚀 End-to-End MLOps Recommendation System

![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![MLflow](https://img.shields.io/badge/MLflow-Tracking-blueviolet)
![Terraform](https://img.shields.io/badge/Terraform-IaC-purple)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)

A complete, end-to-end Machine Learning Operations (MLOps) project that builds, tracks, deploys, and monitors a Recommendation System using Collaborative Filtering (SVD). This project showcases best practices in ML lifecycle management, from model training and tracking to scalable deployment and continuous data drift monitoring.

---

## 📖 Project Overview

This repository contains the infrastructure and code for a movie/item recommendation system. It uses the `surprise` library to train a Singular Value Decomposition (SVD) model on user ratings. 

Key MLOps capabilities included:
* **Experiment Tracking:** Logging hyperparameters, metrics, and models using **MLflow**.
* **Containerized Deployment:** A robust **FastAPI** application to serve predictions, containerized via **Docker**.
* **Infrastructure as Code (IaC):** AWS infrastructure definitions using **Terraform** and tested locally via **LocalStack**.
* **Observability & Monitoring:** Custom scripts to track dataset drift and business metrics, stored in **PostgreSQL** and visualized in **Grafana**.
* **CI/CD:** Automated testing workflows via **GitHub Actions**.

---

## 🏗️ Architecture

The system is designed with a modern, decoupled architecture:

1. **Model Training & Experimentation (`src/train`)**
   * Uses `scikit-surprise` to train an SVD model.
   * Connects to a local/dockerized MLflow tracking server to log runs, RMSE metrics, and save the artifact (`svd_model.pkl`).
2. **Serving Layer (`src/api`)**
   * A FastAPI service with modern lifespan event management to load the ML model into memory at startup.
   * Exposes a `/predict` endpoint that takes a `user_id` and `item_id` and returns a predicted rating.
3. **Data Monitoring (`monitoring`)**
   * Computes statistical differences (drift) between a reference dataset and current traffic.
   * Logs complex metrics (drift score, total ratings, unique users) directly to a PostgreSQL database.
4. **Infrastructure Services (`infrastructure/docker-compose.yml`)**
   * **PostgreSQL:** Acts as the backend store for MLflow and the repository for monitoring metrics.
   * **MLflow Server:** Centralized UI for tracking ML experiments.
   * **Grafana:** Connects to PostgreSQL to visualize system health and data drift over time.
   * **LocalStack:** Simulates AWS services locally for testing serverless deployments (Lambda).

---

## 📂 Folder Structure

```text
recsys-mlops-project/
├── .github/workflows/       # CI/CD pipelines (GitHub Actions)
├── data/                    # Dataset storage (e.g., ratings.csv)
├── infrastructure/          # Infrastructure configurations
│   ├── terraform/           # Terraform IaC files (main.tf)
│   ├── local_artifacts/     # Local storage for MLflow artifacts
│   └── docker-compose.yml   # Multi-container orchestration
├── lambda/                  # AWS Lambda function scripts
├── monitoring/              # Scripts for tracking drift and metrics
│   └── monitor.py           # Custom drift and business metrics logger
├── src/                     # Core application source code
│   ├── api/                 # FastAPI prediction service
│   │   └── app.py
│   ├── data_prep/           # Data cleaning and ingestion scripts
│   └── train/               # Model training scripts
│       └── train.py         # SVD training with MLflow integration
├── tests/                   # Unit and integration tests
├── requirements.txt         # Project dependencies
├── simulate_traffic.py      # Script to simulate API requests
└── svd_model.pkl            # Serialized trained model (Artifact)
```

---

## 🛠️ Technology Stack

* **Machine Learning:** `scikit-surprise` (SVD), `pandas`
* **Model Tracking:** MLflow
* **API Framework:** FastAPI, Uvicorn
* **Database:** PostgreSQL (for MLflow and Metrics)
* **Monitoring UI:** Grafana
* **Containerization:** Docker, Docker Compose
* **Infrastructure as Code:** Terraform, LocalStack (AWS simulation)
* **Testing & CI/CD:** Pytest, GitHub Actions

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Docker & Docker Compose
* (Optional) Terraform

### 1. Local Environment Setup
Clone the repository and install dependencies:
```bash
git clone <your-repo-url>
cd recsys-mlops-project
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the Infrastructure Services
Launch MLflow, PostgreSQL, Grafana, and LocalStack using Docker Compose:
```bash
cd infrastructure
docker-compose up -d
```
* **MLflow UI:** `http://localhost:5001`
* **Grafana UI:** `http://localhost:3001`

### 3. Train the Model
Navigate to the root directory and run the training script. This will log metrics and save the model to MLflow.
```bash
python src/train/train.py
```
*Check the MLflow UI to see the logged metrics, parameters, and saved artifacts.*

### 4. Run the API Server
Start the FastAPI server locally:
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```
* **Interactive API Docs:** `http://localhost:8000/docs`

---

## 📡 API Usage

**Endpoint:** `POST /predict`

**Request Body:**
```json
{
  "user_id": 1,
  "item_id": 105
}
```

**Example cURL:**
```bash
curl -X 'POST' \
  'http://localhost:8000/predict' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "user_id": 1,
  "item_id": 105
}'
```

**Response:**
```json
{
  "user_id": 1,
  "item_id": 105,
  "predicted_rating": 3.75
}
```

---

## 📊 Monitoring & Observability

To simulate the passage of time and incoming data, run the monitoring script:
```bash
python monitoring/monitor.py
```
This script reads subsets of your data, compares reference data against current data, and logs:
* Dataset Drift Score
* Average current ratings
* Unique user counts

These metrics are saved directly into the PostgreSQL database (`evidently_metrics` table) and can be visualized by setting up a dashboard in the local Grafana instance.

---

## 🧪 Testing

To run the unit and integration tests:
```bash
pytest tests/
```
Continuous Integration is configured via `.github/workflows/ci.yml` to automatically run these tests on code pushes.
