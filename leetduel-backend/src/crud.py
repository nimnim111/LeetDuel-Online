from sqlalchemy.orm import Session
from .models import Problem

def get_problem(db: Session, problem_id: int):
    # Ensure that 'id' matches the primary key name in your models
    return db.query(Problem).filter(Problem.problem_id == problem_id).first()

def get_count(db: Session):
    return db.query(Problem).count()

def create_problem(db: Session, title: str, description: str, difficulty: str, test_cases: list, function_signature: str):
    db_problem = Problem(problem_name=title, problem_description=description, problem_difficulty=difficulty, test_cases=test_cases, function_signature=function_signature)  
    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return db_problem