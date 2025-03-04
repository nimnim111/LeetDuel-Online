from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Problem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    description = Column(String)
    difficulty = Column(String)

class Party(Base):
    __tablename__ = "parties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    host_id = Column(Integer, ForeignKey("users.id"))