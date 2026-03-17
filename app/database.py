from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")


# ==========================
# ENGINE (SAFE FOR RENDER)
# ==========================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # prevents stale connections
    pool_recycle=300        # refresh connections every 5 mins
)


# ==========================
# SESSION
# ==========================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==========================
# BASE MODEL
# ==========================
Base = declarative_base()


# ==========================
# DB DEPENDENCY
# ==========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()