# End-to-End MLOps Recommendation System

> A production-grade Machine Learning Operations pipeline that builds, tracks, deploys, and monitors a real-time collaborative filtering recommendation system from scratch.

---

## Project Philosophy

This project was built to demonstrate what a **complete MLOps lifecycle** looks like in practice. It deliberately goes beyond a simple Jupyter notebook — instead, every stage of the ML lifecycle is automated, instrumented, and repeatable:

| Stage | Tool Used |
|---|---|
| Data Ingestion | Python + MovieLens Dataset |
| Model Training | scikit-surprise (SVD) |
| Experiment Tracking | MLflow |
| Model Serving | FastAPI + Uvicorn |
| Containerization | Docker + Docker Compose |
| Infrastructure as Code | Terraform + LocalStack |
| Real-Time Streaming | AWS Kinesis (via LocalStack) |
| Serverless Compute | AWS Lambda (via LocalStack) |
| Data Drift Monitoring | Custom script + PostgreSQL |
| Monitoring Dashboards | Grafana |
| CI/CD | GitHub Actions |

---

## The Problem Being Solved

A user visits a platform and has watched or rated items in the past. The system needs to **predict how much a specific user will enjoy a specific item** — fast enough to be useful in real-time and reliably enough to trust in production.

This project solves that with:
1. A **Collaborative Filtering** model (SVD) trained on historical ratings
2. A **real-time streaming pipeline** (Kinesis → Lambda) to handle live user events
3. A **REST API** for synchronous queries
4. A **monitoring system** to detect when predictions start to drift from expected quality

---

## Full System Architecture

```
╔═══════════════════════════════════════════════════════════════════╗
║                      DATA LAYER                                   ║
║  MovieLens 100K Dataset → data/ratings.csv                        ║
║  (user_id, item_id, rating, timestamp) — ~100,000 interactions    ║
╚═══════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═══════════════════════════════════════════════════════════════════╗
║                     TRAINING PIPELINE                             ║
║  src/train/train.py                                               ║
║  - Loads ratings.csv via pandas                                   ║
║  - Trains SVD model via scikit-surprise (RMSE ≈ 0.97)            ║
║  - Logs params, RMSE metric, and saves svd_model.pkl              ║
║  - Tracked by MLflow (http://localhost:5001)                      ║
╚═══════════════════════════════════════════════════════════════════╝
                              │
                  ┌───────────┴───────────┐
                  ▼                       ▼
╔══════════════════════╗   ╔══════════════════════════════════════╗
║  REST API (Sync)     ║   ║  Streaming Pipeline (Async / RT)    ║
║  src/api/app.py      ║   ║                                      ║
║  FastAPI + Uvicorn   ║   ║  simulate_traffic.py                 ║
║  POST /predict       ║   ║    → Kinesis: recsys-input-events    ║
║  → predicted_rating  ║   ║      (via LocalStack @ :4566)        ║
╚══════════════════════╝   ║        │                             ║
                           ║        ▼                             ║
                           ║  lambda/lambda_function.py           ║
                           ║    → Processes event                 ║
                           ║    → Generates prediction            ║
                           ║    → Pushes to output stream         ║
                           ║        │                             ║
                           ║        ▼                             ║
                           ║  consumer_stream.py                  ║
                           ║    ← Kinesis: recsys-output-...      ║
                           ║    ← Reads & displays recommendations║
                           ╚══════════════════════════════════════╝
                              │
                              ▼
╔═══════════════════════════════════════════════════════════════════╗
║                  MONITORING LAYER                                  ║
║  monitoring/monitor.py                                            ║
║  - Compares reference data (first 50k rows)                       ║
║    vs current data (next 10k rows)                                ║
║  - Calculates: drift_score, avg_rating, unique_users              ║
║  - Writes metrics → PostgreSQL (evidently_metrics table)          ║
║  - Visualized in Grafana (http://localhost:3001)                  ║
╚═══════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═══════════════════════════════════════════════════════════════════╗
║               INFRASTRUCTURE (Docker Compose)                     ║
║  ┌─────────────┐  ┌───────────┐  ┌──────────┐  ┌─────────────┐  ║
║  │ PostgreSQL  │  │  MLflow   │  │ Grafana  │  │ LocalStack  │  ║
║  │  :5444      │  │  :5001    │  │  :3001   │  │  :4566      │  ║
║  └─────────────┘  └───────────┘  └──────────┘  └─────────────┘  ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## Component Deep Dives

### 1. Data Ingestion (`src/data_prep/get_data.py`)

Downloads and preprocesses the **MovieLens 100K** dataset from GroupLens Research.

- **Source:** `http://files.grouplens.org/datasets/movielens/ml-100k.zip`
- **Format:** Tab-separated (user_id, item_id, rating, timestamp)
- **Output:** `data/ratings.csv` — a clean, comma-separated file
- **Auto-cleanup:** Removes the zip and extracted folder after processing

```bash
python src/data_prep/get_data.py
```

---

### 2. Model Training (`src/train/train.py`)

Trains a **Singular Value Decomposition (SVD)** model — a well-established matrix factorization technique for collaborative filtering.

**How SVD works here:**
- The ratings matrix (users × items) is factored into latent vectors
- SVD learns a low-dimensional representation of both users and items
- Prediction = dot product of user vector and item vector + biases

**Hyperparameters logged to MLflow:**

| Parameter | Value | Effect |
|---|---|---|
| `n_factors` | 50 | Dimensionality of latent space |
| `n_epochs` | 20 | Training iterations |
| `lr_all` | 0.005 | Learning rate |
| `reg_all` | 0.02 | Regularization to prevent overfitting |

**What happens during a run:**
1. Reads `data/ratings.csv`
2. Splits 80% train / 20% test (random seed 42 for reproducibility)
3. Trains SVD model
4. Evaluates on test set → logs **RMSE** to MLflow
5. Saves model as `svd_model.pkl` via pickle

```bash
python src/train/train.py
```

---

### 3. REST API — Synchronous Serving (`src/api/app.py`)

A **FastAPI** service that loads the trained model and serves predictions over HTTP.

**Key design decisions:**
- Uses modern **lifespan context manager** (not deprecated `@app.on_event`) to load the model once at startup
- Model is held in memory for fast, stateless inference
- Returns a 503 error (Service Unavailable) if model file isn't found — production-safe behavior

**Endpoint:**
```
POST /predict
Content-Type: application/json

{
  "user_id": 42,
  "item_id": 101
}
```

**Response:**
```json
{
  "user_id": 42,
  "item_id": 101,
  "predicted_rating": 3.84
}
```

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

---

### 4. Real-Time Streaming Pipeline

This is the **most advanced component** of the project, implementing an event-driven, serverless architecture using AWS primitives — all running locally via LocalStack.

#### Data Flow:
```
simulate_traffic.py
    │  (random user/item pairs, every 0.5-2 seconds)
    │
    └──► AWS Kinesis: recsys-input-events (shard_count=1)
              │
              └──► Lambda Trigger (batch_size=100)
                        │
                        ▼
                lambda/lambda_function.py
                    - Decodes Base64 Kinesis payload
                    - Generates predicted rating
                    - Pushes result to output stream
                        │
                        └──► AWS Kinesis: recsys-output-recommendations
                                  │
                                  └──► consumer_stream.py
                                            (polls every 2 seconds, prints results)
```

#### Scripts:
- **`simulate_traffic.py`** — Simulates real users interacting with the platform by sending random `user_id` + `item_id` pairs to the input Kinesis stream
- **`lambda/lambda_function.py`** — The serverless processor. Triggered by Kinesis. Decodes, predicts, and forwards results
- **`consumer_stream.py`** — A real-time consumer that reads from the output Kinesis stream and displays incoming recommendations

---

### 5. Infrastructure as Code (`infrastructure/terraform/main.tf`)

All AWS resources are defined with **Terraform** and provisioned against **LocalStack** (a local AWS cloud emulator) — no real AWS account needed.

**Resources provisioned:**

| Resource | Name | Purpose |
|---|---|---|
| `aws_kinesis_stream` | `recsys-input-events` | Ingests user events |
| `aws_kinesis_stream` | `recsys-output-recommendations` | Delivers recommendations |
| `aws_iam_role` | `recsys_lambda_kinesis_role` | IAM role for Lambda execution |
| `aws_iam_role_policy_attachment` | Kinesis + CloudWatch | Permissions for Lambda |
| `aws_lambda_function` | `recsys-stream-processor` | The serverless prediction function |
| `aws_lambda_event_source_mapping` | Kinesis → Lambda | Connects input stream to Lambda |

**Terraform commands:**
```bash
cd infrastructure/terraform
terraform init
terraform apply -auto-approve
```

---

### 6. Infrastructure Services (`infrastructure/docker-compose.yml`)

Four services are orchestrated together:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `db` | `postgres:14` | 5444 | Backend store for MLflow metadata + monitoring metrics |
| `mlflow` | `python:3.10-slim` | 5001 | MLflow tracking server UI |
| `grafana` | `grafana/grafana:latest` | 3001 | Monitoring dashboards |
| `localstack` | `localstack/localstack:3.7.2` | 4566 | Local AWS cloud emulator |

```bash
cd infrastructure
docker-compose up -d
```

---

### 7. Monitoring & Drift Detection (`monitoring/monitor.py`)

Tracks **data drift** and **business metrics** to detect when the model's operational environment has shifted from its training distribution.

**Metrics Calculated:**

| Metric | Description |
|---|---|
| `dataset_drift` | Boolean — True if drift score > 0.05 |
| `share_of_drifted_columns` | Numeric score of drift magnitude |
| `avg_current_rating` | Mean rating of current window |
| `total_ratings` | Count of ratings in current window |
| `unique_users` | Number of distinct users in current window |

**Data windows:**
- **Reference (baseline):** First 50,000 rows of `ratings.csv`
- **Current (production window):** Rows 50,000 → 60,000

**Output:** Metrics are written to the `evidently_metrics` table in PostgreSQL and can be visualized in Grafana by connecting it to the PostgreSQL data source.

```bash
python monitoring/monitor.py
```

---

### 8. CI/CD Pipeline (`.github/workflows/ci.yml`)

An automated integration test runs on every `push` or `pull_request` to `main`.

**Pipeline Steps:**
1. Checkout repository code
2. Set up Python 3.11 environment
3. Start LocalStack via Docker
4. Set up Terraform
5. Run `terraform apply` to provision Kinesis streams + Lambda
6. Run `test_pipeline.py` — sends a test event to the Kinesis stream and verifies a 200 OK response

This proves that the **infrastructure provisioning is reproducible** and that the **streaming pipeline is functional** in a clean environment.

---

## Folder Structure

```
recsys-mlops-project/
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI/CD pipeline
│
├── data/
│   └── ratings.csv                 # MovieLens 100K dataset (processed)
│
├── infrastructure/
│   ├── docker-compose.yml          # Spins up PostgreSQL, MLflow, Grafana, LocalStack
│   ├── local_artifacts/            # MLflow artifact storage volume
│   └── terraform/
│       ├── main.tf                 # Kinesis streams, Lambda, IAM roles
│       ├── .terraform.lock.hcl     # Provider version lock file
│       └── terraform.tfstate       # Terraform state (current infra state)
│
├── lambda/
│   ├── lambda_function.py          # Serverless prediction processor
│   └── lambda_function.zip         # Packaged deployment artifact
│
├── monitoring/
│   └── monitor.py                  # Data drift + business metrics to PostgreSQL
│
├── src/
│   ├── api/
│   │   └── app.py                  # FastAPI prediction service
│   ├── data_prep/
│   │   └── get_data.py             # Downloads and preprocesses MovieLens data
│   └── train/
│       └── train.py                # SVD model training + MLflow tracking
│
├── tests/                          # Unit test directory
│
├── consumer_stream.py              # Reads recommendations from Kinesis output stream
├── simulate_traffic.py             # Sends random events to Kinesis input stream
├── test_pipeline.py                # CI integration test for Kinesis stream
├── test_stream.py                  # Quick local smoke test for Kinesis
├── svd_model.pkl                   # Trained and serialized SVD model
└── requirements.txt                # All Python dependencies (pinned versions)
```

---

## Development Environment Setup

### Prerequisites
- Python 3.10 or 3.11
- Docker Engine + Docker Compose
- Terraform CLI
- Git

### Full Local Setup

**Step 1: Clone and install dependencies**
```bash
git clone <your-repo-url>
cd recsys-mlops-project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Step 2: Fetch the dataset**
```bash
python src/data_prep/get_data.py
```

**Step 3: Start all infrastructure services**
```bash
cd infrastructure
docker-compose up -d
```
Wait ~15 seconds for services to initialize.

**Step 4: Provision AWS resources on LocalStack**
```bash
cd infrastructure/terraform
terraform init
terraform apply -auto-approve
```

**Step 5: Train the model**
```bash
# From project root
python src/train/train.py
```
View the run at: `http://localhost:5001`

**Step 6: Start the REST API**
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Interactive docs at: `http://localhost:8000/docs`

**Step 7: Start the streaming pipeline (3 terminals)**
```bash
# Terminal 1 — Send user events
python simulate_traffic.py

# Terminal 2 — Run the Lambda function locally (via LocalStack trigger)
# (Lambda is triggered automatically by Kinesis when using Terraform setup)

# Terminal 3 — Consume recommendations
python consumer_stream.py
```

**Step 8: Run monitoring**
```bash
python monitoring/monitor.py
```
View dashboards at: `http://localhost:3001` (admin/admin)

---

## Key Design Decisions

### Why SVD?
SVD (Singular Value Decomposition) is one of the most battle-tested algorithms for collaborative filtering. It won the Netflix Prize in 2009 and balances accuracy, interpretability, and training speed well — making it an ideal choice for demonstrating an end-to-end pipeline without over-engineering the ML component.

### Why LocalStack instead of real AWS?
LocalStack allows testing the full AWS streaming architecture (Kinesis + Lambda) locally without incurring cloud costs or needing credentials. This is a professional MLOps practice — infrastructure should be testable in a local environment before being deployed to production.

### Why FastAPI?
FastAPI provides automatic OpenAPI documentation, native Pydantic validation, and modern async support. The lifespan context manager is used (instead of the deprecated `@app.on_event`) to demonstrate awareness of current best practices.

### Why PostgreSQL for monitoring instead of a file?
Storing metrics in PostgreSQL makes them queryable, persistent, and directly connectable to Grafana — enabling professional-grade dashboards rather than print statements.

---

## Running Tests

```bash
# Unit tests
pytest tests/

# Integration test (requires LocalStack running)
python test_pipeline.py

# Quick Kinesis smoke test
python test_stream.py
```
