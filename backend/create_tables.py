# =====================================================
# Database Initialization Script - Create All Tables
# =====================================================

# Import Base and engine for database schema creation
from database import Base, engine
# Import all models so they are registered with Base metadata
import models

# Create all tables defined in models based on the database schema
# This will generate CREATE TABLE statements for all models
Base.metadata.create_all(bind=engine)

print("Tables created successfully!")