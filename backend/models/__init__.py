"""
Database configuration and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .database import Base

# Database URL - SQLite for POC
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./voice_agent.db")

# Make database path absolute if it's SQLite
if DATABASE_URL.startswith("sqlite:///./"):
    # Get the project root directory (parent of backend)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "voice_agent.db")
    DATABASE_URL = f"sqlite:///{db_path}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get database session for non-FastAPI contexts"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
