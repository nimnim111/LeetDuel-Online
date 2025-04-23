from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

from .dataclass import ProblemData
from typing import cast, List


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

    def asdata(self) -> ProblemData:
        return ProblemData(
            cast(str, self.problem_name),
            cast(str, self.problem_description),
            cast(str, self.function_signature),
            cast(str, self.problem_difficulty),
            cast(List[dict[str, str]], self.test_cases),
            cast(bool, self.any_order),
            cast(int, self.reports)
        )


class Party(Base):
    __tablename__ = "parties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    host_id = Column(Integer, ForeignKey("users.id"))