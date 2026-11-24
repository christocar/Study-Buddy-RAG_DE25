"""Checks that Python can reach Postgres: connects and runs SELECT 1.

Run from the repo root, with the POSTGRES_* values from .env:
    uv run --env-file .env python -m study_buddy.storage.check_connection
"""

import os

import psycopg


def check_connection() -> int:
    """Connect with the settings from the environment and return the result of SELECT 1."""
    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    ) as conn:
        row = conn.execute("SELECT 1").fetchone()
    return row[0]


if __name__ == "__main__":
    print(f"Connected. SELECT 1 returned {check_connection()}")
