# AWS Cloud Deployment Final Exam - Deliverables & Submission Report

**Student Name:** [Your Full Name]  
**Student ID:** [Your Student ID]  
**Course:** Cloud Computing / AWS & DevOps  
**Repository URL:** [Your GitHub Repository URL]  
**EC2 Public Endpoint:** `http://<YOUR-EC2-PUBLIC-IP>`  

---

## Part 1: IAM Configuration (15%)

### Task 1.1: Create IAM User
- **User Name:** `fastapi-deployer`
- **Access Type:** Programmatic access (Access key - CLI, SDK, API)
- **Console Access:** Optional

#### Step-by-Step Execution:
1. Open **AWS Management Console** -> **IAM** -> **Users** -> **Create user**.
2. Set User name to `fastapi-deployer`.
3. Check programmatic access (create access keys under **Security credentials** tab).
4. Download the generated credentials file (`.csv`).
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

---

### Task 1.2: Create and Attach Policies
Create a custom policy named `FastAPIDeploymentPolicy` with the exact permissions required by the exam rubric:

| Service | Actions Required |
|---|---|
| **EC2** | `ec2:DescribeInstances`, `ec2:StartInstances`, `ec2:StopInstances` |
| **S3** | `s3:GetObject`, `s3:PutObject`, `s3:ListBucket`, `s3:DeleteObject` |
| **RDS** | `rds:DescribeDBInstances`, `rds:Connect` |

#### Exact IAM Policy JSON:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2Permissions",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3Permissions",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RDSPermissions",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:Connect"
      ],
      "Resource": "*"
    }
  ]
}
```
Attach `FastAPIDeploymentPolicy` directly to the `fastapi-deployer` user.

---

### Task 1.3: Configure Local AWS CLI
Run on local terminal:
```bash
aws configure
```
Input parameters:
- **AWS Access Key ID:** `<Your Access Key ID>`
- **AWS Secret Access Key:** `<Your Secret Access Key>`
- **Default region name:** `ap-southeast-1`
- **Default output format:** `json`

Verify with caller identity:
```bash
aws sts get-caller-identity
```

#### Output Verification:
```json
{
    "UserId": "AIDXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/fastapi-deployer"
}
```

### Deliverables for Part 1:
- [ ] **Screenshot 1.1:** IAM user creation summary showing user name `fastapi-deployer`
- [ ] **Screenshot 1.2:** Attached policy details showing the exact EC2, S3, RDS permissions
- [ ] **Screenshot 1.3:** Terminal output of `aws sts get-caller-identity`

---

## Part 2: Database Setup with Amazon RDS (20%)

### Task 2.1: Create RDS Instance Specification
Configured in AWS RDS Console:
- **Engine:** PostgreSQL 15.x
- **Instance Class:** `db.t3.micro`
- **Storage:** 20 GB gp2 (Disable autoscaling)
- **DB Instance ID:** `fast-api-db`
- **Master Username:** `postgres`
- **Master Password:** `YourPassword123!`
- **Database Name:** `fastapi-prod`
- **VPC:** Default VPC
- **Public Accessibility:** **Yes**
- **Security Group:** Inbound rule allowing **PostgreSQL (Port 5432)** from `0.0.0.0/0` (or local IP + EC2 security group)

---

### Task 2.2: FastAPI Database Configuration
Configured in `app/database.py` and `.env` using environment variables:
```dotenv
DB_HOST=fast-api-db.cxxxxxxx.ap-southeast-1.rds.amazonaws.com
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=YourPassword123!
DB_NAME=fastapi-prod
DATABASE_URL=postgresql://postgres:YourPassword123!@fast-api-db.cxxxxxxx.ap-southeast-1.rds.amazonaws.com:5432/fastapi-prod
```

---

### Task 2.3: Verify Connectivity to RDS from Local Machine
Execute the diagnostic script:
```bash
python scripts/test_db_connection.py
```

#### Successful Output:
```text
============================================================
 AWS RDS PostgreSQL Connection Test (Task 2.3) 
============================================================
[*] Target Database URL : postgres:****@fast-api-db.cxxxxxxx.ap-southeast-1.rds.amazonaws.com:5432/fastapi-prod
[*] DB Host             : fast-api-db.cxxxxxxx.ap-southeast-1.rds.amazonaws.com
[*] DB Port             : 5432
[*] DB Name             : fastapi-prod
[*] DB User             : postgres
------------------------------------------------------------
[SUCCESS] Successfully connected to database!
[*] Latency         : 41.20 ms
[*] Engine Version  : PostgreSQL 15.4 on x86_64-pc-linux-gnu
------------------------------------------------------------
Status: 200 OK - Database is operational and ready for FastAPI.
============================================================
```

### Deliverables for Part 2:
- [ ] **Screenshot 2.1:** AWS Console RDS instance details (`fast-api-db`, status: Available, endpoint)
- [ ] **Screenshot 2.2:** Terminal output of `python scripts/test_db_connection.py` showing successful connection

---

## Part 3: File Storage with Amazon S3

### Task 3.1: Create S3 Bucket Specification
- **Bucket Name:** `fastapi-app-files-<your-id>` (e.g. `fastapi-app-files-student123`)
- **Region:** `ap-southeast-1` (Singapore)
- **Block Public Access:** **Enabled**
- **Versioning:** **Enabled**

---

### Task 3.2 & 3.3: Implement S3 Upload in FastAPI
- S3 client service: `app/services/s3_service.py` using `boto3`.
- Endpoints:
  - `POST /files/upload` - Uploads file directly to S3 and records file metadata in RDS PostgreSQL.
  - `GET /files` - Lists uploaded files.
  - `GET /files/{id}/download-url` - Returns presigned temporary download URL.

#### Upload Verification via cURL:
```bash
curl -X POST "http://localhost:8000/files/upload" \
  -F "file=@test-image.png"
```

#### Successful Response:
```json
{
  "id": 1,
  "original_filename": "test-image.png",
  "s3_key": "uploads/0c17a541315949d09bf4ec836dbfcfd5.png",
  "s3_url": "https://fastapi-app-files-student123.s3.ap-southeast-1.amazonaws.com/uploads/0c17a541315949d09bf4ec836dbfcfd5.png",
  "file_size": 15420,
  "content_type": "image/png",
  "uploaded_at": "2026-10-07T14:30:00Z"
}
```

Run test verification script:
```bash
python scripts/test_s3_connection.py
```

### Deliverables for Part 3:
- [ ] **Screenshot 3.1:** S3 Bucket configuration in AWS Console (bucket name, region `ap-southeast-1`, versioning enabled)
- [ ] **Screenshot 3.2:** Swagger UI / Postman demonstrating `POST /files/upload` execution
- [ ] **Screenshot 3.3:** AWS S3 Console showing the uploaded file object inside the bucket

---

## Part 4: Containerization with Docker

> **Exam Note:** You will build the docker image directly on the EC2 instance in Part 5. No container registry is required for this exam.

### Task 4.1: Production-Ready Dockerfile
Located at `Dockerfile`:
- Base: `python:3.11-slim`
- Non-root user: `appuser`
- Health check configured on `/health`
- Exposes port `8000`

### Task 4.2: docker-compose.yml
Located at `docker-compose.yml`:
- Defines `api` container and persistent `app_network`.

### Task 4.3: Verify Image & Run Locally
```bash
# 1. Build image locally
docker build -t fastapi-prod-app:latest .

# 2. Run container locally
docker run -d --name fastapi_local_test -p 8000:8000 --env-file .env fastapi-prod-app:latest

# 3. Check container status
docker ps

# 4. Verify API response
curl http://localhost:8000/health

# 5. Clean up
docker stop fastapi_local_test && docker rm fastapi_local_test
```

### Deliverables for Part 4:
- [x] Production `Dockerfile`
- [x] Multi-service `docker-compose.yml`
- [ ] **Screenshot 4.1:** Terminal output of successful `docker build` and `docker run` locally

---

## Part 5: Deploy to Amazon EC2

### Task 5.1: Launch EC2 Instance Specification
- **AMI:** Amazon Linux 2023 or Ubuntu 22.04 LTS
- **Instance Type:** `t2.micro`
- **Key Pair:** `fastapi-key.pem`
- **Storage:** 8 GB gp3
- **Security Group (`fastapi-ec2-sg`):**
  - Inbound SSH (TCP `22`): `0.0.0.0/0` (or your IP)
  - Inbound HTTP (TCP `80`): `0.0.0.0/0`
  - Inbound Custom TCP (TCP `8000`): `0.0.0.0/0`

---

### Task 5.2: SSH into EC2 & Install Software
```bash
chmod 400 fastapi-key.pem
ssh -i "fastapi-key.pem" ubuntu@<EC2-PUBLIC-IP>
```
Run installation on EC2:
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y docker.io git curl
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
newgrp docker
docker --version
```

---

### Task 5.3: Clone Repo, Build Image Directly on EC2 & Run It
```bash
# Clone project repository
git clone https://github.com/<YOUR-USERNAME>/<YOUR-REPO>.git ~/fastapi-aws
cd ~/fastapi-aws

# Build the image directly on the EC2 instance
docker build -t fastapi-prod-app:latest .

# Run container mapped to port 80
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

---

### Task 5.4: Test Deployed App
Verify public access via browser / cURL:
- **Interactive Swagger UI:** `http://<EC2-PUBLIC-IP>/docs`
- **Health Check Endpoint:** `http://<EC2-PUBLIC-IP>/health`
- **Items CRUD Test:**
  ```bash
  curl -X POST "http://<EC2-PUBLIC-IP>/items/" \
    -H "Content-Type: application/json" \
    -d '{"title": "EC2 Production Item", "description": "Verified on EC2"}'
  ```

### Deliverables for Part 5:
- [ ] **Screenshot 5.1:** AWS Console showing running EC2 instance (`fastapi-ec2-server`, t2.micro, Public IP)
- [ ] **Screenshot 5.2:** EC2 Security Group inbound rules (ports 22, 80, 8000)
- [ ] **Screenshot 5.3:** Terminal on EC2 showing `docker ps` with running container `fastapi_cloud_app`
- [ ] **Screenshot 5.4:** Browser showing successful response from `http://<EC2-PUBLIC-IP>/health` and `http://<EC2-PUBLIC-IP>/docs`

---

## Part 6: CI/CD Pipeline with GitHub Actions (15%)

The pipeline SSHes into the EC2 instance, pulls the latest code, rebuilds the Docker image directly on the instance, and restarts the container.

### Task 6.1: Workflow File
Configured at `.github/workflows/deploy.yml`.

### Task 6.2: GitHub Secrets Configuration
In **GitHub Repository** -> **Settings** -> **Secrets and variables** -> **Actions**:

| Secret Name | Description | Value Example |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | IAM User Access Key | `AKIAXXXXXXXXXXXXXXXX` |
| `AWS_SECRET_ACCESS_KEY`| IAM User Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `EC2_HOST` | EC2 Public IPv4 Address | `13.250.xx.xx` |
| `EC2_SSH_KEY` | Private SSH Key for EC2 (`.pem`) | `-----BEGIN RSA PRIVATE KEY-----...` |
| `DATABASE_URL` | Full RDS Connection String | `postgresql://postgres:pass@fast-api-db.cxxxxxxx.ap-southeast-1.rds.amazonaws.com:5432/fastapi-prod` |
| `S3_BUCKET_NAME` | S3 Bucket Name | `fastapi-app-files-<your-id>` |

### Deliverables for Part 6:
- [x] Workflow file `.github/workflows/deploy.yml`
- [ ] **Screenshot 6.1:** GitHub Repository Secrets settings page showing all 6 configured secrets
- [ ] **Screenshot 6.2:** GitHub Actions tab showing green checkmark on successful workflow run
- [ ] **Screenshot 6.3:** GitHub Actions deployment step log showing remote build and container restart on EC2

---

## Final Submission Checklist

- [ ] All source code committed and pushed to GitHub
- [ ] `Dockerfile` and `docker-compose.yml` present in project root
- [ ] `.github/workflows/deploy.yml` present and passing
- [ ] `README.md` complete with all 8 required sections
- [ ] Application running live on Amazon EC2 (Port 80)
- [ ] Amazon RDS PostgreSQL database connected and functional
- [ ] Amazon S3 bucket receiving uploads and returning URLs
- [ ] All required screenshots captured and attached to final report
