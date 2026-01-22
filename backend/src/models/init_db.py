# This is for PostgreSQL stuff now
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# NOTE: This will only work if everyone has a .env file in the root of `backend` named DATABASE_URL=whatever
# To get the database connection string, go on the Discord channel in the #database-information channel
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("No .env file in root!!!!! Add one first, then try it again")

engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)


# This is just a simple test, might delete but it's good for debugging!
def test_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"Connection successful! Test Query Result: {result.first()[0]}")
    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    test_connection()
