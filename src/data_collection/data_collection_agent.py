import os
from pathlib import Path

import psycopg
from psycopg import sql

from dotenv import load_dotenv

import pandas as pd

project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")


def get_connection():
    """Return a secure connection to the Neon PostgreSQL database."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Add the Neon connection string to your .env file."
        )

    return psycopg.connect(database_url)


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


def insert_reading(record: dict):
    """Insert one CSV-shaped reading into robot_readings"""
    values = (
        record["Trait"],
        *(record[f"Axis #{i}"] for i in range(1, 9)),
        record["Time"],
    )
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO robot_readings
                       (trait, axis_1, axis_2, axis_3, axis_4,
                        axis_5, axis_6, axis_7, axis_8, reading_time)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                values,
            )
        connection.commit()
