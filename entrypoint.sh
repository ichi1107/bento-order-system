git#!/bin/bash
set -e

echo "Waiting for database..."

# データベース接続を待機
python -c "
import time
import psycopg2
import sys

for i in range(30):
    try:
        conn = psycopg2.connect(
            host='db', 
            database='bento_db', 
            user='postgres', 
            password='password'
        )
        conn.close()
        print('Database is ready!')
        sys.exit(0)
    except psycopg2.OperationalError:
        print(f'Database not ready, waiting... ({i+1}/30)')
        time.sleep(2)

print('Database connection failed after 30 attempts')
sys.exit(1)
"

echo "Initializing database..."
python init_data.py

echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload