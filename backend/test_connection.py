# Database connection test - tries to connect and run SELECT 1 query
from database import engine
from sqlalchemy import text

try:
    with engine.connect() as connection:  # Establish database connection
        result = connection.execute(text("SELECT 1"))  # Execute test query
        print("Connection successful:", result.fetchone())  # Print result
except Exception as e:
    print("Connection failed:", e)  # Handle and display connection errors