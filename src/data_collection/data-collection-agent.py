

import os
from pathlib import Path

import psycopg
from psycopg import sql

from dotenv import load_dotenv

import pandas as pd


project_root = Path(__file__).resolve().parents[2]

def get_connection():
    """Return a secure connection to the Neon PostgreSQL database."""
    load_dotenv(project_root / ".env.local")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Add the Neon connection string to your .env file."
        )

    return psycopg.connect(database_url)


# Example: read the first five rows from the newly created students table.
with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM robot_readings LIMIT 5;")
        records = cursor.fetchall()

        for record in records:
            print(record)




def fetch_all():
    """Retrieve every row from the robot_readings table as a pandas DataFrame."""

    query = sql.SQL("SELECT * FROM robot_readings").format(
        table=sql.Identifier("robot_readings")
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()
            column_names = [column.name for column in cursor.description]

    return pd.DataFrame(rows, columns=column_names)


# Example usage
readings_df = fetch_all()

print(readings_df)
print(readings_df.head(5))