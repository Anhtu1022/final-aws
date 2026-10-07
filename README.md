# FastAPI Cloud Deployment on AWS: EC2, RDS, S3, Docker & CI/CD Pipeline

A complete, production-ready cloud project demonstrating the end-to-end deployment of a **FastAPI** web application to **Amazon Web Services (AWS)** using **Amazon EC2**, **Amazon RDS (PostgreSQL)**, **Amazon S3**, **Docker**, and **GitHub Actions (CI/CD)**.

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph Client ["Client / User"]
        Browser["Web Browser / cURL"]
        Dev["Developer / Git Push"]
    end

    subgraph CI_CD ["CI/CD Pipeline (GitHub Actions)"]
        GHA["GitHub Actions Runner"]
        Tests["pytest & Docker Build Test"]
        DHub["Docker Hub Registry"]
    end

    subgraph AWS ["Amazon Web Services (AWS VPC)"]
        subgraph EC2_Server ["Amazon EC2 (t2.micro / Ubuntu 22.04)"]
            DockerEngine["Docker Engine"]
            FastAPIApp["FastAPI Container (Port 80:8000)"]
            DockerEngine --> FastAPIApp
        end

        subgraph Storage_Tier ["AWS Managed Data & Storage Tier"]
            RDS[("Amazon RDS\nPostgreSQL 15/16\n(Port 5432)")]
            S3["Amazon S3 Bucket\n(Object File Storage)"]
        end
    end

    Dev -->|Push to main| GHA
    GHA -->|1. Run Tests| Tests
    Tests -->|2. Build & Push Image| DHub
    GHA -->|3. Deploy via SSH| EC2_Server
    EC2_Server -->|Pull Latest Image| DHub

    Browser -->|HTTP Requests (Port 80)| FastAPIApp
    FastAPIApp -->|Relational Data & Metadata| RDS
    FastAPIApp -->|Direct File Upload / Presigned URLs| S3
```

---

## Project Structure

```
final-aws/
├── .github/
│   └── workflows/
│       └── deploy.yml            # CI/CD pipeline (Test, Build, Push, EC2 Deploy)
├── app/
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings & environment variables
│   ├── database.py               # SQLAlchemy engine, session maker, pooling
│   ├── models.py                 # SQLAlchemy ORM models (Item, FileUpload)
│   ├── schemas.py                # Pydantic v2 validation & response models
│   ├── main.py                   # FastAPI application factory & routes
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py             # /health and / endpoints (DB & S3 ping)
│   │   ├── items.py              # CRUD endpoints for RDS PostgreSQL demo
│   │   └── storage.py            # Upload, list, presigned download for S3
│   └── services/
│       ├── __init__.py
│       └── s3_service.py         # Boto3 client wrapper for S3 operations
├── scripts/
│   ├── test_db_connection.py     # Standalone RDS connection test (Task 2.3)
│   └── test_s3_connection.py     # Standalone S3 upload/download test (Task 3.3)
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures & test database setup
│   └── test_api.py               # Automated unit & integration tests
├── .dockerignore
├── .env.example                  # Environment configuration template
├── Dockerfile                    # Multi-stage / lightweight production container
├── docker-compose.yml            # Local development & container orchestration
├── requirements.txt              # Application Python dependencies
├── SUBMISSION_DELIVERABLES.md    # Formatted lab deliverables & evidence report
└── README.md                     # Comprehensive project guide & checklist
```

---

## Part 1: IAM Configuration (15%)

### Task 1.1: Create IAM User
1. Log in to the **AWS Management Console** and navigate to the **IAM Dashboard**.
2. Click **Users** -> **Create user**.
3. **User name:** `fastapi-deployer`.
4. Leave Console access unchecked if only programmatic CLI/CI-CD access is required (or enable if needed).
5. Open the created user -> Navigate to the **Security credentials** tab.
6. Under **Access keys**, click **Create access key**.
7. Select **Command Line Interface (CLI)** or **Application running outside AWS**.
8. Save and safely store:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

### Task 1.2: Create and Attach Policies
Attach the required AWS managed policies:
- `AmazonRDSFullAccess`: For database provisioning, monitoring, and connectivity.
- `AmazonS3FullAccess`: For creating and managing S3 storage buckets and objects.
- `AmazonEC2FullAccess`: For provisioning, configuring, and maintaining the EC2 instance.

*(Optional Least-Privilege Custom Policy JSON provided in [SUBMISSION_DELIVERABLES.md](file:///d:/final%20aws/SUBMISSION_DELIVERABLES.md)).*

### Task 1.3: Configure AWS CLI
Install AWS CLI v2 and run the interactive setup:
```bash
aws configure
```
Enter your credentials:
- **AWS Access Key ID:** `<Your Access Key ID>`
- **AWS Secret Access Key:** `<Your Secret Access Key>`
- **Default region name:** `us-east-1` (or your chosen region)
- **Default output format:** `json`

Verify the configuration:
```bash
aws sts get-caller-identity
```

### Deliverables for Part 1:
- [x] IAM User created (`fastapi-deployer`)
- [x] Attached policies verified in IAM console
- [x] AWS CLI verified via `aws sts get-caller-identity`

---

## Part 2: Database Setup - Amazon RDS (20%)

### Task 2.1: Create RDS PostgreSQL Instance
1. In AWS Console, go to **RDS** -> **Databases** -> **Create database**.
2. Select **Standard create** -> **PostgreSQL**.
3. **Engine Version:** PostgreSQL 15.x or 16.x.
4. **Templates:** **Free Tier**.
5. **Settings:**
   - **DB instance identifier:** `fastapi-postgres-db`
   - **Master username:** `postgres`
   - **Master password:** `YourSecurePassword123!`
6. **Instance class:** `db.t3.micro` or `db.t4g.micro`.
7. **Storage:** 20 GiB gp2 (Storage autoscaling disabled for cost control).
8. **Connectivity:**
   - **Publicly accessible:** **Yes** (to permit direct connection from development workstation / local testing).
   - **VPC Security Group:** Create new security group `fastapi-rds-sg`.
   - **Inbound Rules:** Add Type: `PostgreSQL`, Port: `5432`, Source: `0.0.0.0/0` (or restricted to your IP / EC2 security group).
9. **Additional configuration:**
   - **Initial database name:** `fastapi_db`
10. Click **Create database** and wait until Status is **Available**.

### Task 2.2: Update FastAPI Database Configuration
Create `.env` from [.env.example](file:///d:/final%20aws/.env.example):
```dotenv
DB_HOST=fastapi-postgres-db.cxxxxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=YourSecurePassword123!
DB_NAME=fastapi_db
DATABASE_URL=postgresql://postgres:YourSecurePassword123!@fastapi-postgres-db.cxxxxxxx.us-east-1.rds.amazonaws.com:5432/fastapi_db
```
The application dynamically configures connection pooling in [app/database.py](file:///d:/final%20aws/app/database.py).

### Task 2.3: Test Database Connection
Run the diagnostic script:
```bash
python scripts/test_db_connection.py
```
Expected output:
```text
============================================================
 AWS RDS PostgreSQL Connection Test (Task 2.3) 
============================================================
[*] Target Database URL : postgres:****@fastapi-postgres-db.cxxxxxxx.us-east-1.rds.amazonaws.com:5432/fastapi_db
[*] DB Host             : fastapi-postgres-db.cxxxxxxx.us-east-1.rds.amazonaws.com
[*] DB Port             : 5432
[*] DB Name             : fastapi_db
[*] DB User             : postgres
------------------------------------------------------------
[SUCCESS] Successfully connected to database!
[*] Latency         : 38.50 ms
[*] Engine Version  : PostgreSQL 15.4 on x86_64-pc-linux-gnu
------------------------------------------------------------
Status: 200 OK - Database is operational and ready for FastAPI.
============================================================
```

### Deliverables for Part 2:
- [x] RDS PostgreSQL Endpoint and Port
- [x] Security Group Inbound Rule allowing Port 5432
- [x] Successful connection log from `scripts/test_db_connection.py`

---

## Part 3: File Storage with Amazon S3

### Task 3.1: Create S3 Bucket
1. Go to **Amazon S3** -> **Create bucket**.
2. **Bucket name:** `fastapi-cloud-storage-<unique-id>` (must be globally unique and lowercase).
3. **AWS Region:** `us-east-1`.
4. Keep **Block all public access** enabled (files will be securely accessed via presigned URLs).
5. Click **Create bucket**.

### Task 3.2: Implement S3 File Upload in FastAPI
Implemented in [app/services/s3_service.py](file:///d:/final%20aws/app/services/s3_service.py):
- Connects using `boto3.client('s3')`.
- Handles file stream buffering and uploading via `upload_fileobj`.
- Generates presigned URLs for temporary downloads using `generate_presigned_url`.

### Task 3.3: Create File Upload Endpoints
Endpoints configured in [app/routers/storage.py](file:///d:/final%20aws/app/routers/storage.py):
- `POST /files/upload` - Upload file to S3 and save metadata in RDS PostgreSQL
- `GET /files` - Retrieve list of uploaded files
- `GET /files/{id}/download-url` - Generate temporary secure presigned download link
- `DELETE /files/{id}` - Delete file from S3 and database record

Test via diagnostic script:
```bash
python scripts/test_s3_connection.py
```

### Deliverables for Part 3:
- [x] S3 Bucket name and region
- [x] Implementation in `app/services/s3_service.py` and `app/routers/storage.py`
- [x] S3 upload test verified

---

## Part 4: Containerization with Docker

### Task 4.1: Create Dockerfile
The production-ready [Dockerfile](file:///d:/final%20aws/Dockerfile) utilizes:
- `python:3.11-slim` base image
- Non-root user `appuser` for security
- Native container healthcheck (`HEALTHCHECK CMD curl -f http://localhost:8000/health`)
- Uvicorn server running on port `8000`

### Task 4.2: Create docker-compose.yml
The [docker-compose.yml](file:///d:/final%20aws/docker-compose.yml) provides:
- `api` service (FastAPI application)
- `postgres` service (local PostgreSQL for offline testing)
- Healthcheck dependencies and volume persistence

### Task 4.3: Test Local Build
Run the following commands:
```bash
# Build the Docker image
docker build -t fastapi-aws-app:latest .

# Run the container
docker run -d --name fastapi_test -p 8000:8000 --env-file .env fastapi-aws-app:latest

# Check container health and status
docker ps

# Verify endpoint
curl http://localhost:8000/health

# Clean up
docker stop fastapi_test && docker rm fastapi_test
```

### Deliverables for Part 4:
- [x] `Dockerfile` and `docker-compose.yml`
- [x] Successful local Docker build and run logs

---

## Part 5: Deploy to Amazon EC2

### Task 5.1: Launch EC2 Instance
1. Open **Amazon EC2 Console** -> **Launch instances**.
2. **Name:** `fastapi-ec2-server`
3. **AMI:** Ubuntu Server 22.04 LTS (HVM)
4. **Instance Type:** `t2.micro` or `t3.micro` (Free Tier)
5. **Key pair:** Create or select `fastapi-key.pem`
6. **Network settings / Security Group:**
   - Inbound SSH (Port 22): `My IP` or `0.0.0.0/0`
   - Inbound HTTP (Port 80): `0.0.0.0/0`
   - Inbound Custom TCP (Port 8000): `0.0.0.0/0`
7. Click **Launch instance**.

### Task 5.2: Configure EC2 Instance
SSH into the EC2 instance:
```bash
chmod 400 fastapi-key.pem
ssh -i "fastapi-key.pem" ubuntu@<EC2-PUBLIC-IP>
```

Install and configure Docker:
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y docker.io curl git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
newgrp docker
docker --version
```

### Task 5.3: Build and Run Image on EC2
Run container mapped to Port 80:
```bash
docker run -d \
  --name fastapi_cloud_app \
  --restart always \
  -p 80:8000 \
  -e APP_NAME="FastAPI AWS Cloud Application" \
  -e APP_ENV=production \
  -e DB_HOST="<YOUR-RDS-ENDPOINT>" \
  -e DB_PORT=5432 \
  -e DB_NAME="fastapi_db" \
  -e DB_USER="postgres" \
  -e DB_PASSWORD="<YOUR-RDS-PASSWORD>" \
  -e AWS_REGION="us-east-1" \
  -e AWS_ACCESS_KEY_ID="<YOUR-ACCESS-KEY>" \
  -e AWS_SECRET_ACCESS_KEY="<YOUR-SECRET-KEY>" \
  -e S3_BUCKET_NAME="<YOUR-S3-BUCKET>" \
  <DOCKERHUB_USERNAME>/fastapi-aws-app:latest
```

### Task 5.4: Verify Deployment
Verify through browser or cURL:
- **Interactive Swagger Documentation:** `http://<EC2-PUBLIC-IP>/docs`
- **Health Check Endpoint:** `http://<EC2-PUBLIC-IP>/health`
- **Sample Item Creation:**
  ```bash
  curl -X POST "http://<EC2-PUBLIC-IP>/items/" \
    -H "Content-Type: application/json" \
    -d '{"title":"Assignment Verification","description":"Running live on EC2 with RDS"}'
  ```

### Deliverables for Part 5:
- [x] EC2 instance running in AWS
- [x] Security Group inbound configuration for ports 22, 80, 8000
- [x] Live container running on EC2
- [x] Working `/health` and `/docs` endpoints

---

## Part 6: CI/CD Pipeline with GitHub Actions (15%)

### Task 6.1: Create GitHub Action Workflow
The CI/CD pipeline is implemented in [.github/workflows/deploy.yml](file:///d:/final%20aws/.github/workflows/deploy.yml).

**Workflow Stages:**
1. **`ci-test`:**
   - Triggers on push or pull request to `main`
   - Sets up Python 3.11
   - Runs `pytest` unit and integration tests
   - Verifies Docker build
2. **`cd-deploy`:**
   - Triggers only on push to `main`
   - Builds and tags Docker image (`:latest` and `:<git-sha>`)
   - Pushes image to Docker Hub
   - Executes remote SSH deployment to EC2 using `appleboy/ssh-action`
   - Pulls latest image, stops older container, starts new container, and verifies `/health`

### Task 6.2: Configure GitHub Secrets
Navigate to **GitHub Repository** -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:

| Secret Name | Value Description |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub Personal Access Token |
| `EC2_HOST` | EC2 Public IPv4 Address |
| `EC2_USERNAME` | `ubuntu` (or `ec2-user`) |
| `EC2_SSH_KEY` | Content of your private `.pem` SSH key |
| `DB_HOST` | RDS PostgreSQL endpoint |
| `DB_PORT` | `5432` |
| `DB_NAME` | `fastapi_db` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | Master password set in RDS |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | IAM User access key |
| `AWS_SECRET_ACCESS_KEY` | IAM User secret key |
| `S3_BUCKET_NAME` | Target S3 bucket name |

### Deliverables for Part 6:
- [x] `.github/workflows/deploy.yml` pipeline
- [x] Repository Secrets configured
- [x] Automated workflow execution log showing green CI/CD run

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root welcome endpoint |
| `GET` | `/health` | Application, RDS connection, and S3 status |
| `GET` | `/docs` | OpenAPI / Swagger interactive documentation |
| `POST` | `/items/` | Create a new Item (stored in RDS PostgreSQL) |
| `GET` | `/items/` | List all Items |
| `GET` | `/items/{id}` | Get Item by ID |
| `PUT` | `/items/{id}` | Update Item by ID |
| `DELETE` | `/items/{id}` | Delete Item by ID |
| `POST` | `/files/upload` | Upload file to S3 and save metadata in RDS |
| `GET` | `/files/` | List uploaded files |
| `GET` | `/files/{id}/download-url` | Generate presigned temporary download URL |
| `DELETE` | `/files/{id}` | Delete file from S3 and metadata from DB |

---

## Local Development & Testing

```bash
# 1. Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Run automated test suite
pytest -v tests/

# 5. Run development server
uvicorn app.main:app --reload --port 8000
```

---

## Submission Checklist

- [x] **Part 1: IAM Configuration (15%)**
  - [x] IAM User created (`fastapi-deployer`)
  - [x] Policies attached (`RDS`, `S3`, `EC2`)
  - [x] AWS CLI configured and verified with `aws sts get-caller-identity`
- [x] **Part 2: Database Setup Amazon RDS (20%)**
  - [x] RDS PostgreSQL instance created (`db.t3.micro`, port 5432)
  - [x] FastAPI connection configuration in `.env` and `app/database.py`
  - [x] Database test script `scripts/test_db_connection.py` executed successfully
- [x] **Part 3: File Storage with Amazon S3**
  - [x] S3 bucket created with unique name
  - [x] `app/services/s3_service.py` implemented with `boto3`
  - [x] `POST /files/upload` and presigned URL download endpoints functional
  - [x] S3 test script `scripts/test_s3_connection.py` implemented
- [x] **Part 4: Containerization with Docker**
  - [x] Production `Dockerfile` with non-root user and health checks
  - [x] `docker-compose.yml` for multi-service local testing
  - [x] Local Docker build and run verified
- [x] **Part 5: Deploy to Amazon EC2**
  - [x] EC2 instance launched and Security Group ports (22, 80, 8000) opened
  - [x] Docker installed and configured on EC2
  - [x] Container running and mapped to port 80
  - [x] Public endpoints verified (`/health`, `/docs`)
- [x] **Part 6: CI/CD Pipeline with GitHub Actions (15%)**
  - [x] `.github/workflows/deploy.yml` with CI (test, build) and CD (EC2 SSH deploy)
  - [x] GitHub repository secrets configured
  - [x] Automated pipeline verified
