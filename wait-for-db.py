#!/usr/bin/env python
"""Wait for PostgreSQL to be ready"""
import sys
import time
import os
import psycopg

DB_HOST = os.getenv('DB_HOST', 'db')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'clubpro_db')
DB_USER = os.getenv('DB_USER', 'clubpro_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'clubpro_password')

max_attempts = 30
attempt = 0

print("Waiting for postgres...")

while attempt < max_attempts:
    try:
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.close()
        print("PostgreSQL started!")
        sys.exit(0)
    except Exception as e:
        attempt += 1
        if attempt < max_attempts:
            print(f"Postgres is unavailable - sleeping (attempt {attempt}/{max_attempts})")
            time.sleep(1)
        else:
            print(f"Failed to connect to PostgreSQL after {max_attempts} attempts")
            sys.exit(1)
