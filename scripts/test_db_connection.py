#!/usr/bin/env python3
"""
Task 2.3: Test Database Connection Script.
Connects to the configured AWS RDS PostgreSQL instance, executes a test query,
and prints diagnostic output for lab submission deliverables.
"""
import sys
import os
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.config import get_settings
from app.database import engine

def test_database():
    settings = get_settings()
    db_url = settings.get_database_url()

    # Mask password for display
    masked_url = db_url
    if "@" in db_url and ":" in db_url.split("@")[0]:
        parts = db_url.split("@")
        cred_parts = parts[0].rsplit(":", 1)
        masked_url = f"{cred_parts[0]}:****@{parts[1]}"

    print("=" * 60)
    print(" AWS RDS PostgreSQL Connection Test (Task 2.3) ")
    print("=" * 60)
    print(f"[*] Target Database URL : {masked_url}")
    print(f"[*] DB Host             : {settings.DB_HOST or '(From URL or local)'}")
    print(f"[*] DB Port             : {settings.DB_PORT}")
    print(f"[*] DB Name             : {settings.DB_NAME or '(default)'}")
    print(f"[*] DB User             : {settings.DB_USER or '(default)'}")
    print("-" * 60)

    start_time = time.time()
    try:
        with engine.connect() as connection:
            if "postgresql" in db_url:
                query = text("SELECT version();")
            else:
                query = text("SELECT sqlite_version();")

            result = connection.execute(query)
            db_version = result.scalar()
            latency = (time.time() - start_time) * 1000

            print("[SUCCESS] Successfully connected to database!")
            print(f"[*] Latency         : {latency:.2f} ms")
            print(f"[*] Engine Version  : {db_version}")
            print("-" * 60)
            print("Status: 200 OK - Database is operational and ready for FastAPI.")
            print("=" * 60)
            return 0
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        print(f"[ERROR] Failed to connect to database! ({latency:.2f} ms)")
        print(f"Detail: {str(e)}")
        print("-" * 60)
        print("Troubleshooting Tips:")
        print(" 1. Check RDS Security Group: Inbound rule for Port 5432 must allow EC2 / local IP.")
        print(" 2. Check RDS 'Publicly Accessible' setting if testing from local machine.")
        print(" 3. Verify DB_HOST, DB_USER, DB_PASSWORD, DB_NAME in .env file.")
        print(" 4. Verify RDS DB Instance Status is 'Available'.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(test_database())
