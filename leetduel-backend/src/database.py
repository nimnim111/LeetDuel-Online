from sqlalchemy import create_engine, MetaData, Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from .config import database_url
from datetime import datetime

Base = declarative_base()

class UserRank(Base):
    __tablename__ = "user_ranks"
    
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True)  # Firebase UID
    username = Column(String)
    email = Column(String)
    total_score = Column(Float, default=0)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()