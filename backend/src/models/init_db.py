# This is for PostgreSQL stuff now.
# NO NEED TO RUN THIS!! I already did so the database is fine now....
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from contextlib import contextmanager
from typing import Generator

from src.models.database import Base

load_dotenv()


# NOTE: This will only work if everyone has a .env file in the root of `backend` named DATABASE_URL=whatever
# To get the database connection string, go on the Discord channel in the #database-information channel
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("No .env file in root!!!!! Add one first, then try it again")

engine = create_engine(DATABASE_URL)

# This is like.. a pool? So that everytime we make queries it doesn't slow down
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    print("Starting database build...")
    # Database table imports hehe got this from `database.py`
    from src.models.orm import (
        Project,
        File,
        Language,
        Contributor,
        ContributorFile,
        Complexity,
        Skill,
        ProjectSkill,
        ProjectSkillSummary,
        ProjectSkillTimeline,
        ResumeItem,
        Framework,
        ProjectFramework,
        Library,
        ProjectLibrary,
        Tool,
        ProjectTool,
        Config,
        UserProfile,
        WorkExperience,
    )

    Base.metadata.create_all(bind=engine)


# This is just a simple test, might delete but it's good for debugging!
def test_connection():
    try:
        with engine.connect():
            print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    test_connection()
    init_db()
