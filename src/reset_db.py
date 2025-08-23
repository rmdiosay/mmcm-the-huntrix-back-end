from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DB_NAME = "postgres"

# Create engine connected to default 'postgres' system db
admin_engine = create_engine("postgresql://postgres:postgres@localhost:5432/template1", isolation_level="AUTOCOMMIT")

with admin_engine.connect() as conn:
    # Kick out active connections first
    conn.execute(text(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{DB_NAME}'
          AND pid <> pg_backend_pid();
    """))

    # Drop and recreate
    conn.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME}"))
    conn.execute(text(f"CREATE DATABASE {DB_NAME}"))