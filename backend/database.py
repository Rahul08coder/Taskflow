# =====================================================
# Database Configuration - Connection Setup
# =====================================================

import os
from dotenv import load_dotenv  # Load environment variables from .env file
from sqlalchemy import create_engine  # Create database engine for connection
from sqlalchemy.orm import sessionmaker, declarative_base  # ORM components

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create database engine - handles connection pooling and database communication
engine = create_engine(DATABASE_URL)

# Create session factory - generates database sessions for transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models - all models inherit from this
Base = declarative_base()

# Dependency function to get database session - used in FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db  # Provide session to endpoint
    finally:
        db.close()  # Always close session after use