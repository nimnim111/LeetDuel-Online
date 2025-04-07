from sqlalchemy.orm import Session
from .models import Problem
import random


def get_problem(db: Session, difficulties: list[bool], problem_id: int = None) -> Problem:
    if problem_id is not None:
        return db.query(Problem).filter(Problem.problem_id == problem_id).first()
    enabled_difficulties = []
    if difficulties[0]:
        enabled_difficulties.append("Easy")
    if difficulties[1]:
        enabled_difficulties.append("Medium")
    if difficulties[2]:
        enabled_difficulties.append("Hard")
    problems = db.query(Problem).filter(Problem.problem_difficulty.in_(enabled_difficulties)).all()
    if not problems:
        return None
    return random.choice(problems)


def get_count(db: Session):
    return db.query(Problem).count()


def create_problem(db: Session, title: str, description: str, difficulty: str, test_cases: list, function_signature: str, any_order: bool):
    db_problem = Problem(problem_name=title, problem_description=description, problem_difficulty=difficulty, test_cases=test_cases, function_signature=function_signature, any_order=any_order, reports=0)  
    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return db_problem


def check_problem_exists(db: Session, title: str) -> bool:
    return db.query(Problem).filter(Problem.problem_name == title).first() is not None

def increment_reports(db: Session, title: int):
    problem = db.query(Problem).filter(Problem.problem_name == title).first()
    if problem:
        problem.reports = problem.reports + 1
        db.commit()
        db.refresh(problem)