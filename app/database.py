from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy_utils import database_exists, create_database

from app.config import DATABASE_URL

# Create Database Automatically
if not database_exists(DATABASE_URL):
    create_database(DATABASE_URL)
    print("Database Created Successfully")
else:
    print("Database Already Exists")

# Connect to Database
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()