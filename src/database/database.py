import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = "postgresql://postgres:{}@db.engepyysrjkmhxkumyit.supabase.co:5432/postgres"

passw = os.environ.get("supabase_pass", "")

if not passw:
    raise EnvironmentError("Missing environment variable: 'supabase_pass'")

try:
    engine = create_engine(SUPABASE_URL.format(passw))
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base = declarative_base()
except Exception as e:
    raise RuntimeError(f"Failed to initialise database: {e}") from e


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()