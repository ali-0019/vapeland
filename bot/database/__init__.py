"""
Database module for the Vapeland Telegram bot.
Handles database connections and operations.
"""

# This file marks the 'database' directory as a Python package
# It allows importing modules from this directory

from sqlalchemy import create_engine
from .models import Base
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def init_database():
    """Initialize the database by creating all tables."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()
