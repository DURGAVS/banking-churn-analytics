"""
Database configuration.

Credentials are read from a .env file which is NEVER committed to git.
Create your .env by copying .env.example and filling in your own values.
"""
# Passwords containing @ or : break the connection URL, since those
# characters are separators. quote_plus percent-encodes them.
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# Find the project root (one level up from config/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load the .env file
load_dotenv(PROJECT_ROOT / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "bank_analytics")

# Useful paths, so no script has to hardcode a folder
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOG_DIR = PROJECT_ROOT / "logs"


def get_engine():
    """Return a SQLAlchemy engine connected to the MySQL database."""
    url = (
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    return create_engine(url, pool_pre_ping=True)


def test_connection():
    """Quick check that the database is reachable."""
    from sqlalchemy import text
    try:
        with get_engine().connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).scalar()
        print(f"Connected to MySQL {version}  (database: {DB_NAME})")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
