import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

_engine = None
_SessionLocal = None

def get_engine():
    """Create database engine (lazy initialization)"""
    global _engine
    
    if _engine is not None:
        return _engine
    
    passw = os.environ.get("supabase_pass", "")
    if not passw:
        raise EnvironmentError("Missing env var: supabase_pass")
    
    url = f"postgresql://postgres:{passw}@db.engepyysrjkmhxkumyit.supabase.co:5432/postgres"
    
    
    _engine = create_engine(
        url,
        pool_pre_ping=True, 
        pool_recycle=3600,   
        connect_args={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
        },
    )
    
    return _engine

def get_session_local():
    """Get or create SessionLocal with lazy initialization"""
    global _SessionLocal
    
    if _SessionLocal is not None:
        return _SessionLocal
    
    engine = get_engine()
    _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionLocal

def get_db():
    """Dependency for FastAPI endpoints"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()