from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Problem
from ..crud import create_problem

router = APIRouter(prefix="/problems", tags=["problems"])

@router.get("", response_model=None)
def list_problems(db: Session = Depends(get_db)):
    return db.query(Problem).all()

@router.post("", response_model=None)
def create_problem_api(title: str, description: str, difficulty: str, test_cases: list, function_signature: str):
    db = Depends(get_db)
    return create_problem(db, title, description, difficulty, test_cases, function_signature)