from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

from .types import ProblemData


Base = declarative_base()

class Problem(Base):
    __tablename__ = "problems"
    problem_id = Column(Integer, primary_key=True, index=True)
    problem_name = Column(String, unique=True, index=True)
    problem_description = Column(String)
    problem_difficulty = Column(String)
    test_cases = Column(JSONB)
    function_signature = Column(String)
    any_order = Column(Boolean)
    reports = Column(Integer)


    def asdata(self):
        return ProblemData(self.problem_name, self.problem_description, self.function_signature, self.problem_difficulty, self.test_cases, self.any_order, self.reports)


class Party(Base):
    __tablename__ = "parties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    host_id = Column(Integer, ForeignKey("users.id"))