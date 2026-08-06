import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from app.core.logging import logger

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.db import models
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created.")

def log_node_execution(node_name: str, input_snapshot: dict, output_snapshot: dict, latency_ms: int = 0, complaint_id: str = None):
    """Writes an entry to extraction_logs table for auditability."""
    try:
        from app.db.models import ExtractionLog
        db = SessionLocal()
        try:
            log_entry = ExtractionLog(
                complaint_id=complaint_id,
                node_name=node_name,
                input_snapshot=input_snapshot,
                output_snapshot=output_snapshot,
                latency_ms=latency_ms
            )
            db.add(log_entry)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not write extraction log for {node_name}: {e}")
