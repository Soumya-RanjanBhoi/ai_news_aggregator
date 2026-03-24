import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

def get_engine():
    passw = os.environ.get("supabase_pass", "")
    if not passw:
        raise EnvironmentError("Missing env var: supabase_pass")
    url = f"postgresql://postgres:{passw}@db.engepyysrjkmhxkumyit.supabase.co:5432/postgres"
    return create_engine(url)

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()