# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+psycopg2://postgres:1234@localhost/handme_fastapi.db"  # Update credentials as needed

# Synchronous database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the declarative base class
Base = declarative_base()

# Dependency for FastAPI to use
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
