from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# ==========================
# LOAD ENV
# ==========================
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")


# ==========================
# ENGINE CONFIG (SMART 🔥)
# ==========================
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 300
}

# 🔥 Fix for PostgreSQL on Render (SSL issue)
if DATABASE_URL.startswith("postgresql"):
    engine_kwargs["connect_args"] = {"sslmode": "require"}

# 🔥 Fix for SQLite (dev mode)
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)


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