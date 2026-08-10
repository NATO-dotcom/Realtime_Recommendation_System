<div align="center">

# Realtime Recommendation System — MLOps Pipeline

**An end-to-end MLOps project demonstrating the complete ML lifecycle: from data ingestion and experiment tracking to real-time streaming, serverless inference, and production monitoring.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MLflow](https://img.shields.io/badge/MLflow-Tracking-0194E2?style=flat-square&logo=mlflow&logoColor=white)](https://mlflow.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?style=flat-square&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Grafana](https://img.shields.io/badge/Grafana-Monitoring-F46800?style=flat-square&logo=grafana&logoColor=white)](https://grafana.com/)
[![CI/CD](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/features/actions)

</div>

---

## Overview

This repository contains a production-grade recommendation system built on the **MovieLens 100K** dataset. It uses **Singular Value Decomposition (SVD)** — a battle-tested collaborative filtering algorithm — to predict how much a given user will enjoy a given item.

The focus of this project is not the model itself, but **everything surrounding it**: the infrastructure, tooling, and operational practices that transform an offline ML experiment into a system that can be deployed, monitored, and maintained reliably.

### Key Capabilities

| Capability | Implementation |
|---|---|
| Data Ingestion | Automated download and preprocessing of MovieLens 100K |
| Model Training | SVD via `scikit-surprise` with reproducible hyperparameters |
| Experiment Tracking | MLflow — logs params, metrics, and model artifacts per run |
| Synchronous Serving | FastAPI REST endpoint (`POST /predict`) |
| Real-Time Streaming | AWS Kinesis → Lambda → Kinesis (via LocalStack) |
| Infrastructure as Code | Terraform provisions all cloud resources declaratively |
| Data Drift Monitoring | Custom script computes drift metrics and writes to PostgreSQL |
| Observability | Grafana dashboards connected to PostgreSQL |
| Continuous Integration | GitHub Actions — provisions infra and runs integration tests on every push |

---

## Architecture

The system exposes predictions through two parallel paths:

```
                        ┌──────────────────────────────────┐
                        │         DATA LAYER               │
                        │  MovieLens 100K → ratings.csv    │
                        │  ~100,000 user-item interactions │
                        └────────────────┬─────────────────┘
                                         │
                                         ▼
                        ┌──────────────────────────────────┐
                        │       TRAINING PIPELINE          │
                        │  src/train/train.py              │
                        │  SVD · RMSE Evaluation · MLflow  │
                        │  Output: svd_model.pkl           │
                        └──────────┬───────────────────────┘
                                   │
               ┌───────────────────┴───────────────────┐
               ▼                                       ▼
  ┌─────────────────────────┐          ┌───────────────────────────────┐
  │   REST API (Sync)       │          │   Streaming Pipeline (Async)  │
  │   src/api/app.py        │          │                               │
  │   FastAPI + Uvicorn     │          │  simulate_traffic.py          │
  │   POST /predict         │          │    └─► Kinesis: input-events  │
  │   → predicted_rating    │          │              │                │
  └─────────────────────────┘          │              ▼                │
                                       │    lambda_function.py         │
                                       │    (AWS Lambda via LocalStack)│
                                       │              │                │
                                       │              ▼                │
                                       │    Kinesis: output-recs       │
                                       │              │                │
                                       │              ▼                │
                                       │    consumer_stream.py         │
                                       └───────────────────────────────┘
                                                      │
                                                      ▼
                        ┌──────────────────────────────────────────┐
                        │           MONITORING LAYER               │
                        │  monitoring/monitor.py                   │
                        │  Drift Score · Avg Rating · User Count   │
                        │  → PostgreSQL → Grafana Dashboards       │
                        └──────────────────────────────────────────┘

           ┌──────────────────────────────────────────────────────────┐
           │          INFRASTRUCTURE  (Docker Compose)                │
           │  PostgreSQL :5444  │  MLflow :5001  │  Grafana :3001     │
           │  LocalStack :4566  (AWS Cloud Emulator)                  │
           └──────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
recsys-mlops-project/
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions — provisions infra + integration test
│
├── data/
│   └── ratings.csv                 # Processed MovieLens 100K dataset
│
├── infrastructure/
│   ├── docker-compose.yml          # PostgreSQL, MLflow, Grafana, LocalStack
│   ├── local_artifacts/            # MLflow artifact storage (mounted as volume)
│   └── terraform/
│       ├── main.tf                 # Kinesis streams, Lambda function, IAM roles
│       └── .terraform.lock.hcl    # Provider version lock
│
├── lambda/
│   ├── lambda_function.py          # Serverless stream processor (event → prediction)
│   └── lambda_function.zip         # Packaged deployment artifact
│
├── monitoring/
│   └── monitor.py                  # Computes drift metrics → writes to PostgreSQL
│
├── src/
│   ├── api/
│   │   └── app.py                  # FastAPI service — loads model, serves /predict
│   ├── data_prep/
│   │   └── get_data.py             # Downloads and preprocesses MovieLens dataset
│   └── train/
│       └── train.py                # SVD training script with MLflow integration
│
├── tests/                          # Unit and integration tests
├── consumer_stream.py              # Polls Kinesis output stream, prints recommendations
├── simulate_traffic.py             # Generates random events → pushes to Kinesis input
├── test_pipeline.py                # CI integration test — validates Kinesis connectivity
├── test_stream.py                  # Local smoke test for the streaming pipeline
├── svd_model.pkl                   # Serialized trained model artifact
└── requirements.txt                # Pinned Python dependencies
```

---

## Technology Stack

**Machine Learning**
- [`scikit-surprise`](https://surpriselib.com/) — SVD collaborative filtering
- `pandas`, `numpy` — Data manipulation

**Model Serving**
- [`FastAPI`](https://fastapi.tiangolo.com/) + `Uvicorn` — Async REST API
- `Pydantic` — Request/response validation

**Experiment Tracking**
- [`MLflow`](https://mlflow.org/) — Hyperparameter logging, metric tracking, artifact storage

**Streaming & Serverless**
- AWS Kinesis — Event streaming (input and output)
- AWS Lambda — Serverless stream processor
- [`LocalStack`](https://localstack.cloud/) — Local AWS cloud emulator

**Infrastructure**
- [`Docker`](https://www.docker.com/) + Docker Compose — Container orchestration
- [`Terraform`](https://www.terraform.io/) — Infrastructure as Code

**Data & Observability**
- `PostgreSQL` — MLflow backend store + monitoring metrics storage
- [`Grafana`](https://grafana.com/) — Monitoring dashboards

**CI/CD**
- GitHub Actions — Automated testing on every push to `main`

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker Engine + Docker Compose
- Terraform CLI

### Step 1 — Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd recsys-mlops-project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2 — Fetch the Dataset

```bash
python src/data_prep/get_data.py
```

This downloads MovieLens 100K, converts it to CSV, and saves it to `data/ratings.csv`.

### Step 3 — Start Infrastructure Services

```bash
cd infrastructure
docker-compose up -d
```

| Service | URL |
|---|---|
| MLflow UI | http://localhost:5001 |
| Grafana | http://localhost:3001 |
| LocalStack (AWS) | http://localhost:4566 |
| PostgreSQL | localhost:5444 |

Wait ~15 seconds for all services to initialize before proceeding.

### Step 4 — Provision Cloud Resources (LocalStack)

```bash
cd infrastructure/terraform
terraform init
terraform apply -auto-approve
```

This creates the two Kinesis streams, the Lambda function, and the required IAM roles — all locally via LocalStack.

### Step 5 — Train the Model

```bash
# From the project root
python src/train/train.py
```

View the logged run at **http://localhost:5001** — parameters, RMSE metric, and the saved artifact are all tracked.

### Step 6 — Start the REST API

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation is available at **http://localhost:8000/docs**.

### Step 7 — Run the Streaming Pipeline

Open three separate terminals:

```bash
# Terminal 1 — Simulate incoming user events
python simulate_traffic.py

# Terminal 2 — Consume outgoing recommendations
python consumer_stream.py

# Terminal 3 — Run monitoring and log metrics
python monitoring/monitor.py
```

---

## API Reference

### `POST /predict`

Predicts the rating a user would give to a specific item.

**Request**

```json
{
  "user_id": 42,
  "item_id": 101
}
```

**Response**

```json
{
  "user_id": 42,
  "item_id": 101,
  "predicted_rating": 3.84
}
```

**cURL Example**

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 42, "item_id": 101}'
```

**Error Responses**

| Status | Condition |
|---|---|
| `200 OK` | Prediction returned successfully |
| `503 Service Unavailable` | Model file not found at startup |

---

## Monitoring

The monitoring script computes data drift by comparing two windows of the dataset:

| Window | Rows | Purpose |
|---|---|---|
| Reference (baseline) | First 50,000 rows | Represents training-time distribution |
| Current (production) | Rows 50,000–60,000 | Represents live traffic |

**Metrics written to PostgreSQL (`evidently_metrics` table):**

| Metric | Description |
|---|---|
| `dataset_drift` | Boolean — `True` if drift score exceeds threshold |
| `share_of_drifted_columns` | Numeric magnitude of the drift |
| `avg_current_rating` | Mean rating in the current window |
| `total_ratings` | Total events in the current window |
| `unique_users` | Distinct users seen in the current window |

Connect Grafana to the PostgreSQL data source to visualize trends over time. Default credentials: `admin` / `admin`.

---

## CI/CD

The GitHub Actions pipeline runs on every push or pull request to `main`:

1. Starts LocalStack in Docker
2. Initializes and applies Terraform configuration
3. Runs `test_pipeline.py` — sends a test event to the Kinesis stream and asserts a successful response

This guarantees that the infrastructure configuration and streaming pipeline remain functional on every commit.

```bash
# Run tests locally
pytest tests/
python test_pipeline.py
```

---

## License

This project is open-source and available under the [MIT License](LICENSE).
