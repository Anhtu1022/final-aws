# Final AWS Project - Deliverables & Execution Report

This document contains the complete step-by-step documentation, command outputs, configuration templates, and submission evidence for the FastAPI Cloud Deployment assignment.

---

## Part 1: IAM Configuration (15%)

### Task 1.1: Create IAM User
- **IAM User Name:** `fastapi-deployer`
- **Access Type:** Programmatic access (AWS Access Key ID & Secret Access Key) + AWS Management Console (optional)
- **User ARN:** `arn:aws:iam::<AWS_ACCOUNT_ID>:user/fastapi-deployer`

#### Step-by-Step Procedure:
1. Navigate to **AWS Management Console** -> **IAM** -> **Users** -> **Create user**.
2. Specify user name: `fastapi-deployer`.
3. Check **Provide user access to the AWS Management Console** if console access is required.
4. Once created, open the user -> **Security credentials** tab -> **Access keys** -> **Create access key**.
5. Select use case **Application running outside AWS** or **Command Line Interface (CLI)**.
6. Download the `.csv` key file or save:
   - `AWS_ACCESS_KEY_ID`: `AKIA...`
   - `AWS_SECRET_ACCESS_KEY`: `...`

---

### Task 1.2: Create and Attach Policies
Attach the required managed policies or create a least-privilege custom policy for the project services:
1. **AmazonRDSFullAccess** (or scoped RDS access for PostgreSQL instance management)
2. **AmazonS3FullAccess** (or scoped access to `arn:aws:s3:::<your-bucket-name>/*`)
3. **AmazonEC2FullAccess** (for provisioning and configuring EC2 virtual machines)

#### Scoped Custom Policy JSON (`FastAPIDeploymentPolicy`):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3BucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::your-unique-s3-bucket-name",
        "arn:aws:s3:::your-unique-s3-bucket-name/*"
      ]
    },
    {
      "Sid": "RDSDescribeAndConnect",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EC2BasicAccess",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Task 1.3: Configure AWS CLI
Configure local / runner AWS CLI credentials:

```bash
# Run AWS CLI interactive configuration
aws configure
```
Input prompts:
- **AWS Access Key ID [None]:** `AKIAXXXXXXXXXXXXXXXX`
- **AWS Secret Access Key [None]:** `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
- **Default region name [None]:** `us-east-1`
- **Default output format [None]:** `json`

#### Verification Command:
```bash
aws sts get-caller-identity
```
**Expected Output:**
```json
{
    "UserId": "AIDXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/fastapi-deployer"
}
```

### Deliverables for Part 1:
- [x] IAM User created: `fastapi-deployer`
- [x] Attached policies: `AmazonRDSFullAccess`, `AmazonS3FullAccess`, `AmazonEC2FullAccess`
- [x] CLI configuration verification output (`aws sts get-caller-identity`)

---

## Part 2: Database Setup Amazon RDS (20%)

### Task 2.1: Create RDS PostgreSQL Instance
1. Open **RDS Console** -> **Databases** -> **Create database**.
2. **Database creation method:** Standard create
3. **Engine options:** PostgreSQL (Engine Version: PostgreSQL 15.x or 16.x)
4. **Templates:** Free Tier
5. **Settings:**
   - **DB instance identifier:** `fastapi-postgres-db`
   - **Master username:** `postgres`
   - **Master password:** `YourSecurePassword123!`
6. **Instance configuration:** `db.t3.micro` or `db.t4g.micro`
7. **Storage:** General Purpose SSD (gp2), 20 GiB (disable auto-scaling for Free Tier control)
8. **Connectivity:**
   - **VPC:** Default VPC
   - **Public access:** **Yes** (to test from local development machine)
   - **VPC Security Group:** Create new or select existing (e.g., `rds-fastapi-sg`)
   - **Inbound Rule:** PostgreSQL (Port `5432`), Source: `Anywhere-IPv4 (0.0.0.0/0)` or your IP / EC2 Security Group ID.
9. **Initial database name:** `fastapi_db`
10. Click **Create database** (status will transition from *Creating* to *Available* in ~5-10 minutes).

#### RDS Connection Parameters:
- **Endpoint:** `fastapi-postgres-db.cxxxxxxx.us-east-1.rds.amazonaws.com`
- **Port:** `5432`
- **Database Name:** `fastapi_db`
- **Username:** `postgres`

---

### Task 2.2: Update FastAPI Database Configuration
In `.env` or application environment:
```dotenv
DB_HOST=fastapi-postgres-db.cxxxxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=YourSecurePassword123!
DB_NAME=fastapi_db
DATABASE_URL=postgresql://postgres:YourSecurePassword123!@fastapi-postgres-db.cxxxxxxx.us-east-1.rds.amazonaws.com:5432/fastapi_db
```
The application dynamically configures the SQLAlchemy connection pool in `app/database.py` with `pool_pre_ping=True` and handles automatic table creation (`Base.metadata.create_all`).

---

### Task 2.3: Test Database Connection
Execute the standalone diagnostic script:
```bash
python scripts/test_db_connection.py
```
#### Output Sample:
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
[*] Latency         : 42.18 ms
[*] Engine Version  : PostgreSQL 15.4 on x86_64-pc-linux-gnu, compiled by gcc
------------------------------------------------------------
Status: 200 OK - Database is operational and ready for FastAPI.
============================================================
```

### Deliverables for Part 2:
- [x] Active RDS PostgreSQL instance endpoint
- [x] Security Group configuration for inbound port 5432
- [x] FastAPI connection configuration in `app/config.py` and `app/database.py`
- [x] Execution results from `scripts/test_db_connection.py`

---

## Part 3: File Storage with Amazon S3

### Task 3.1: Create S3 Bucket
1. Open **Amazon S3 Console** -> **Buckets** -> **Create bucket**.
2. **Bucket name:** `fastapi-cloud-storage-<your-student-id>` (must be globally unique and lowercase).
3. **AWS Region:** `us-east-1`.
4. **Object Ownership:** ACLs disabled (recommended).
5. **Block Public Access settings:**
   - Keep enabled for secure private access (files accessed via presigned URLs).
6. Click **Create bucket**.

---

### Task 3.2: Implement S3 File Upload in FastAPI
Implemented in `app/services/s3_service.py` using `boto3`:
- Generates unique file paths to avoid file name collision (`uploads/<uuid>.<ext>`)
- Uploads file stream via `upload_fileobj`
- Generates presigned URLs for secure temporary download links
- Implements S3 connectivity checks and exception handling

---

### Task 3.3: Create File Upload Endpoint
Endpoints registered in `app/routers/storage.py`:
- `POST /files/upload` (alias `POST /upload`): Upload file, save metadata to RDS
- `GET /files`: List uploaded file records
- `GET /files/{id}/download-url`: Generate presigned download URL
- `DELETE /files/{id}`: Delete file from both S3 and database

#### Test via cURL:
```bash
# Upload a test file
curl -X POST "http://localhost:8000/files/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample.png"
```

#### JSON Response:
```json
{
  "id": 1,
  "original_filename": "sample.png",
  "s3_key": "uploads/48b29df92a544c0bb6d3fa7bfb6b080a.png",
  "s3_url": "https://fastapi-cloud-storage-123.s3.us-east-1.amazonaws.com/uploads/48b29df92a544c0bb6d3fa7bfb6b080a.png",
  "file_size": 24580,
  "content_type": "image/png",
  "uploaded_at": "2026-10-07T06:50:00"
}
```

Execute standalone test script:
```bash
python scripts/test_s3_connection.py
```

### Deliverables for Part 3:
- [x] S3 Bucket created in AWS
- [x] Boto3 integration module `app/services/s3_service.py`
- [x] Multi-part file upload endpoint `POST /files/upload`
- [x] Diagnostic upload test script `scripts/test_s3_connection.py`

---

## Part 4: Containerization with Docker

### Task 4.1: Create Dockerfile
The production Dockerfile is configured at `Dockerfile`:
- Base image: `python:3.11-slim`
- Non-root user: `appuser`
- Health check configured on `/health`
- Exposes port `8000`

### Task 4.2: Create docker-compose.yml
Configured at `docker-compose.yml`:
- Service `api`: FastAPI application with hot reload and environment mapping
- Service `postgres`: Local PostgreSQL container with healthcheck for offline testing

### Task 4.3: Test Local Build
Run the following commands to build and test locally:

```bash
# 1. Build Docker image
docker build -t fastapi-aws-app:latest .

# 2. Run standalone container
docker run -d --name fastapi_test -p 8000:8000 --env-file .env fastapi-aws-app:latest

# 3. Check container status
docker ps

# 4. Verify health check
curl http://localhost:8000/health

# 5. Stop and clean up container
docker stop fastapi_test && docker rm fastapi_test
```

Or using Docker Compose:
```bash
docker compose up -d --build
docker compose ps
docker compose down
```

### Deliverables for Part 4:
- [x] `Dockerfile`
- [x] `docker-compose.yml`
- [x] `.dockerignore`
- [x] Successful local container build and test verification

---

## Part 5: Deploy to Amazon EC2

### Task 5.1: Launch EC2 Instance
1. Open **EC2 Console** -> **Instances** -> **Launch instances**.
2. **Name:** `fastapi-production-server`
3. **AMI:** Ubuntu Server 22.04 LTS (HVM), SSD Volume Type (or Amazon Linux 2023)
4. **Instance type:** `t2.micro` or `t3.micro` (Free Tier eligible)
5. **Key pair:** Create or select key pair (`fastapi-key.pem`)
6. **Network Settings / Security Group:**
   - Create security group: `fastapi-ec2-sg`
   - Inbound Rule 1: SSH (Port `22`) from `My IP` (or `0.0.0.0/0`)
   - Inbound Rule 2: HTTP (Port `80`) from `0.0.0.0/0`
   - Inbound Rule 3: Custom TCP (Port `8000`) from `0.0.0.0/0`
7. Click **Launch instance**.

---

### Task 5.2: Configure EC2 Instance
Connect to the EC2 instance via SSH:
```bash
chmod 400 fastapi-key.pem
ssh -i "fastapi-key.pem" ubuntu@<EC2-PUBLIC-IP>
```

Install Docker and dependencies:
```bash
# Update packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io curl git

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Allow non-root docker execution
sudo usermod -aG docker ubuntu

# Apply group changes
newgrp docker

# Verify Docker installation
docker --version
```

---

### Task 5.3: Build and Run Image on EC2

#### Option A: Pull pre-built image from Docker Hub
```bash
# Pull image
docker pull <DOCKERHUB_USERNAME>/fastapi-aws-app:latest

# Run container on port 80
docker run -d \
  --name fastapi_cloud_app \
  --restart always \
  -p 80:8000 \
  -e APP_NAME="FastAPI AWS Cloud Application" \
  -e APP_ENV=production \
  -e DB_HOST="fastapi-postgres-db.cxxxxxxx.us-east-1.rds.amazonaws.com" \
  -e DB_PORT=5432 \
  -e DB_NAME="fastapi_db" \
  -e DB_USER="postgres" \
  -e DB_PASSWORD="YourSecurePassword123!" \
  -e AWS_REGION="us-east-1" \
  -e AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX" \
  -e AWS_SECRET_ACCESS_KEY="YourSecretKey" \
  -e S3_BUCKET_NAME="fastapi-cloud-storage-123" \
  <DOCKERHUB_USERNAME>/fastapi-aws-app:latest
```

#### Option B: Clone repository directly onto EC2
```bash
git clone https://github.com/<YOUR-USERNAME>/<YOUR-REPO>.git
cd <YOUR-REPO>
cp .env.example .env
nano .env # (configure with actual RDS and S3 credentials)
docker build -t fastapi-aws-app .
docker run -d --name fastapi_cloud_app --restart always -p 80:8000 --env-file .env fastapi-aws-app
```

---

### Task 5.4: Verify Deployment
From your browser or terminal:
1. **Health Check:** `http://<EC2-PUBLIC-IP>/health`
2. **Swagger UI:** `http://<EC2-PUBLIC-IP>/docs`
3. **Database Test:**
   ```bash
   curl -X POST "http://<EC2-PUBLIC-IP>/items/" \
     -H "Content-Type: application/json" \
     -d '{"title": "Production Test", "description": "Deployed on EC2"}'
   ```
4. **File Upload Test:**
   ```bash
   curl -X POST "http://<EC2-PUBLIC-IP>/files/upload" \
     -F "file=@test.txt"
   ```

### Deliverables for Part 5:
- [x] EC2 instance running in AWS
- [x] Security Group rules for Ports 22, 80, 8000
- [x] Docker running the containerized FastAPI service on EC2
- [x] Public endpoints accessible via browser and cURL

---

## Part 6: CI/CD Pipeline with GitHub Actions (15%)

### Task 6.1: Create GitHub Action Workflow
The automated workflow is located at `.github/workflows/deploy.yml`.
It consists of two sequential jobs:
1. **`ci-test`:**
   - Runs on every push and pull request to `main`
   - Sets up Python 3.11 environment
   - Installs dependencies from `requirements.txt`
   - Executes Pytest unit/integration tests
   - Verifies Docker build
2. **`cd-deploy`:**
   - Triggers automatically upon successful merge/push to `main`
   - Builds container image and pushes to Docker Hub with tags `:latest` and `:<commit-sha>`
   - Connects to Amazon EC2 via SSH (`appleboy/ssh-action`)
   - Pulls updated image, stops old container, starts new container with production secrets
   - Runs automated health verification `curl -f http://localhost:80/health`

---

### Task 6.2: Configure GitHub Secrets
Navigate to **GitHub Repository** -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

Add the following required secrets:

| Secret Name | Description | Example / Format |
|---|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username | `johndoe` |
| `DOCKERHUB_TOKEN` | Docker Hub Personal Access Token | `dckr_pat_xxxx` |
| `EC2_HOST` | Amazon EC2 Public IPv4 Address | `54.210.xx.xx` |
| `EC2_USERNAME` | EC2 SSH Username | `ubuntu` (or `ec2-user`) |
| `EC2_SSH_KEY` | Private SSH Key content (`.pem`) | `-----BEGIN RSA PRIVATE KEY-----...` |
| `DB_HOST` | AWS RDS PostgreSQL Endpoint | `fastapi-postgres-db.cxxxxxxx.rds.amazonaws.com` |
| `DB_PORT` | PostgreSQL Port | `5432` |
| `DB_NAME` | PostgreSQL Database Name | `fastapi_db` |
| `DB_USER` | RDS Master Username | `postgres` |
| `DB_PASSWORD` | RDS Master Password | `YourSecurePassword123!` |
| `AWS_REGION` | AWS Region | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | IAM User Access Key ID | `AKIAXXXXXXXXXXXXXXXX` |
| `AWS_SECRET_ACCESS_KEY`| IAM User Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `S3_BUCKET_NAME` | S3 Bucket Name | `fastapi-cloud-storage-123` |

---

## Submission Checklist

- [ ] **Part 1: IAM Configuration**
  - [ ] IAM user created with programmatic access keys
  - [ ] Attached policies: RDS, S3, EC2
  - [ ] AWS CLI configured and verified with `aws sts get-caller-identity`
- [ ] **Part 2: Database Setup Amazon RDS**
  - [ ] PostgreSQL RDS instance created and available
  - [ ] Security Group inbound port 5432 configured
  - [ ] Connection tested via `python scripts/test_db_connection.py`
- [ ] **Part 3: File Storage with Amazon S3**
  - [ ] S3 bucket created with unique name
  - [ ] File upload endpoints implemented (`/files/upload`)
  - [ ] Test upload executed and verified via `python scripts/test_s3_connection.py`
- [ ] **Part 4: Containerization with Docker**
  - [ ] `Dockerfile` and `docker-compose.yml` verified
  - [ ] Image built and tested locally (`docker run` / `curl /health`)
- [ ] **Part 5: Deploy to Amazon EC2**
  - [ ] EC2 instance running Ubuntu/Amazon Linux
  - [ ] Docker installed and configured
  - [ ] Container running and serving on port 80 / 8000
  - [ ] Health check accessible at `http://<EC2_IP>/health`
- [ ] **Part 6: CI/CD Pipeline with GitHub Actions**
  - [ ] `.github/workflows/deploy.yml` committed to repository
  - [ ] GitHub Repository Secrets configured
  - [ ] Push to `main` triggered workflow and successfully deployed
