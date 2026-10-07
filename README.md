# FastAPI AWS Cloud Deployment - EC2, RDS, S3, Docker & CI/CD Pipeline

A production-ready cloud project demonstrating the automated deployment of a **FastAPI** web application to **Amazon Web Services (AWS)** using **Amazon EC2**, **Amazon RDS (PostgreSQL)**, **Amazon S3**, **Docker**, and **GitHub Actions (CI/CD)**.

---

## 1. Project Overview

This project implements and deploys a high-performance **FastAPI** REST API integrated with AWS managed cloud services:
- **Compute:** Containerized application running on an **Amazon EC2** (`t2.micro`) instance.
- **Database:** Managed **Amazon RDS PostgreSQL 15.x** database storing application data and file metadata.
- **Object Storage:** **Amazon S3** bucket in the `ap-southeast-1` region with bucket versioning enabled.
- **Containerization:** Production Docker image built directly on the EC2 host (no external container registry required).
- **Automation:** **GitHub Actions** CI/CD pipeline that tests code, connects to EC2 via SSH, rebuilds the container, and restarts the service with zero manual intervention.

---

## 2. Architecture Diagram

```mermaid
flowchart TD
    subgraph Users ["Client & Developer"]
        Developer["Developer\n(Git Push main)"]
        Client["Browser / cURL Client"]
    end

    subgraph GitHub ["GitHub Cloud"]
        Repo["GitHub Repository"]
        GHA["GitHub Actions Runner\n(pytest & build test)"]
    end

    subgraph AWS_Cloud ["Amazon Web Services (ap-southeast-1)"]
        subgraph EC2 ["Amazon EC2 Instance (t2.micro)"]
            DockerDaemon["Docker Engine"]
            FastAPI["FastAPI App Container\n(Port 80:8000)"]
            DockerDaemon --> FastAPI
        end

        subgraph Managed_Services ["AWS Managed Data Tier"]
            RDS[("Amazon RDS\nPostgreSQL 15.x\n(fast-api-db / Port 5432)\nDatabase: fastapi-prod")]
            S3["Amazon S3 Bucket\nfastapi-app-files-*\n(Versioning Enabled)"]
        end
    end

    Developer -->|git push origin main| Repo
    Repo -->|Trigger Workflow| GHA
    GHA -->|SSH Deploy & Rebuild on Host| EC2

    Client -->|HTTP Port 80| FastAPI
    FastAPI -->|Relational Queries & Metadata| RDS
    FastAPI -->|Object Storage & Presigned URLs| S3
```

---

## 3. Prerequisites

Before starting, ensure you have the following installed and configured:
- **Python 3.11+** installed on local workstation
- **Docker & Docker Compose** installed
- **AWS CLI v2** installed
- **Active AWS Account** with administrative permissions to create IAM users, RDS, S3, and EC2
- **GitHub Account** to host repository and run GitHub Actions

---

## 4. Local Deployment Setup

### Step 1: Clone Repository & Virtual Environment
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

python -m venv .venv

.venv\Scripts\Activate.ps1

source .venv/bin/activate


pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(If testing locally without cloud RDS/S3, the application automatically falls back to local SQLite).*

### Step 3: Run Automated Test Suite
```bash
pytest -v tests/
```

### Step 4: Run Application Locally
```bash
uvicorn app.main:app --reload --port 8000
```
- Open Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Open Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### Step 5: Test Docker Build Locally (Task 4.3)
```bash
docker build -t fastapi-prod-app:latest .
docker run -d --name fastapi_test -p 8000:8000 --env-file .env fastapi-prod-app:latest
docker ps
curl http://localhost:8000/health
docker stop fastapi_test && docker rm fastapi_test
```

---

## 5. AWS Resources

| Resource | Specification & Settings |
|---|---|
| **IAM User** | Name: `fastapi-deployer` \| Access: Programmatic access (Access Keys) |
| **IAM Permissions** | **EC2:** `DescribeInstances`, `StartInstances`, `StopInstances`<br>**S3:** `GetObject`, `PutObject`, `ListBucket`, `DeleteObject`<br>**RDS:** `DescribeDBInstances`, `Connect` |
| **Amazon RDS** | **Engine:** PostgreSQL 15.x \| **Class:** `db.t3.micro` \| **Storage:** 20GB gp2<br>**DB ID:** `fast-api-db` \| **Master User:** `postgres`<br>**DB Name:** `fastapi-prod` \| **Public Access:** Yes \| **Port:** 5432 |
| **Amazon S3** | **Bucket Name:** `fastapi-app-files-<your-id>` \| **Region:** `ap-southeast-1`<br>**Block Public Access:** Enabled \| **Versioning:** Enabled |
| **Amazon EC2** | **AMI:** Ubuntu 22.04 LTS (or Amazon Linux 2023) \| **Type:** `t2.micro`<br>**Storage:** 8GB gp3 \| **Security Group:** Ports 22 (SSH), 80 (HTTP), 8000 (Custom TCP) |

---

## 6. Environment Variables

The application requires the following environment variables:

| Variable | Description | Example Value |
|---|---|---|
| `APP_NAME` | Name of the FastAPI application | `"FastAPI AWS Cloud Application"` |
| `APP_ENV` | Application environment (`local`, `production`) | `production` |
| `PORT` | Container internal listening port | `8000` |
| `DATABASE_URL` | Full PostgreSQL connection string | `postgresql://postgres:pass@fast-api-db.cxxxxxxx.ap-southeast-1.rds.amazonaws.com:5432/fastapi-prod` |
| `AWS_REGION` | AWS Region for S3 and services | `ap-southeast-1` |
| `AWS_ACCESS_KEY_ID` | IAM User Access Key ID | `AKIAXXXXXXXXXXXXXXXX` |
| `AWS_SECRET_ACCESS_KEY` | IAM User Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `S3_BUCKET_NAME` | Target S3 bucket name | `fastapi-app-files-student123` |

---

## 7. Deployment Instructions

### 7.1 EC2 Instance Provisioning & Software Setup
1. Launch an EC2 instance (`t2.micro`, Ubuntu 22.04) with Security Group opening ports **22**, **80**, and **8000**.
2. Connect to EC2 via SSH:
   ```bash
   chmod 400 fastapi-key.pem
   ssh -i "fastapi-key.pem" ubuntu@<EC2-PUBLIC-IP>
   ```
3. Install Docker and Git on EC2:
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   sudo apt-get install -y docker.io git curl
   sudo systemctl enable --now docker
   sudo usermod -aG docker ubuntu
   newgrp docker
   docker --version
   ```

### 7.2 Manual Deployment on EC2 (Task 5.3)
Build directly on the instance (no external registry required):
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git ~/fastapi-aws
cd ~/fastapi-aws

docker build -t fastapi-prod-app:latest .

docker run -d \
  --name fastapi_cloud_app \
  --restart always \
  -p 80:8000 \
  -e APP_NAME="FastAPI AWS Cloud Application" \
  -e APP_ENV=production \
  -e DATABASE_URL="postgresql://postgres:YourPassword123!@fast-api-db.cxxxxxxx.ap-southeast-1.rds.amazonaws.com:5432/fastapi-prod" \
  -e AWS_REGION="ap-southeast-1" \
  -e AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX" \
  -e AWS_SECRET_ACCESS_KEY="YourSecretKey" \
  -e S3_BUCKET_NAME="fastapi-app-files-<your-id>" \
  fastapi-prod-app:latest
```

### 7.3 Automated CI/CD Setup with GitHub Actions
1. Open your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Add the 6 required repository secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `EC2_HOST`
   - `EC2_SSH_KEY`
   - `DATABASE_URL`
   - `S3_BUCKET_NAME`
3. Push changes to `main` branch:
   ```bash
   git push origin main
   ```
4. The pipeline automatically tests, SSHes into EC2, pulls changes, rebuilds the container, and verifies health check at `http://<EC2-PUBLIC-IP>/health`.

---

## 8. API Documentation

| HTTP Method | Route | Description | Auth / Access |
|---|---|---|---|
| `GET` | `/` | API status and root greeting | Public |
| `GET` | `/health` | Cloud connectivity health check (RDS + S3) | Public |
| `GET` | `/docs` | OpenAPI / Swagger interactive documentation | Public |
| `POST` | `/items/` | Create Item (writes to RDS PostgreSQL) | Public |
| `GET` | `/items/` | List all Items from RDS PostgreSQL | Public |
| `GET` | `/items/{id}` | Get Item by ID | Public |
| `PUT` | `/items/{id}` | Update Item by ID | Public |
| `DELETE` | `/items/{id}` | Delete Item by ID | Public |
| `POST` | `/files/upload` | Upload file to S3 and save metadata to RDS | Multipart Form |
| `GET` | `/files/` | List all uploaded files | Public |
| `GET` | `/files/{id}/download-url` | Generate temporary presigned S3 URL | Public |
| `DELETE` | `/files/{id}` | Delete file from S3 and record from RDS | Public |

### Example cURL Commands:
```bash
curl http://<EC2-PUBLIC-IP>/health

curl -X POST "http://<EC2-PUBLIC-IP>/items/" \
  -H "Content-Type: application/json" \
  -d '{"title": "Assignment Item", "description": "Verified on AWS RDS"}'

curl -X POST "http://<EC2-PUBLIC-IP>/files/upload" \
  -F "file=@sample.png"
