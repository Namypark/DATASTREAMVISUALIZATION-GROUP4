import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# CSV path for the dataset
project_root = Path(__file__).resolve().parents[2]
csv_path = project_root / "data" / "RMBR4-2_export_test.csv"


# Load the Neon connection string from .env.local
load_dotenv(project_root / ".env.local")
database_url = os.environ["DATABASE_URL"]

# Tell SQLAlchemy to use the psycopg driver.
database_url = database_url.replace(
    "postgresql://",
    "postgresql+psycopg://",
    1
)

# Connect to Neon.
engine = create_engine(database_url)

# Test the connection.
with engine.connect() as connection:
    version = connection.execute(text("SELECT version()")).scalar()
    print("Connected to Neon!")
    print(version)

# Read the local CSV file.
data = pd.read_csv(csv_path)

# Create a Neon table named robot_readings and upload the CSV rows.
data.to_sql("robot_readings", engine, if_exists="fail", index=False)

print("CSV data was uploaded to the robot_readings table.")
