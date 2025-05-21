from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Problem
from .database import UserRank
from typing import List, Optional
import random


def get_problem(db: Session, difficulties: list[bool], problem_id: int | None = None) -> Problem | None:
    if problem_id is not None:
        return db.query(Problem).filter(Problem.problem_id == problem_id).first()
    enabled_difficulties: List[str] = []
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

def check_problem_reports(db: Session, title: str) -> int:
    reports = db.query(Problem.reports).filter(Problem.problem_name == title).scalar()
    return reports if reports is not None else 0

def increment_reports(db: Session, title: str) -> None:
    reports = db.query(Problem.reports).filter(Problem.problem_name == title).scalar()
    if reports is not None:
        db.query(Problem).filter(Problem.problem_name == title).update({"reports": reports + 1})
        db.commit()

def get_user_rank(db: Session, uid: str) -> Optional[UserRank]:
    return db.query(UserRank).filter(UserRank.uid == uid).first()

def get_top_players(db: Session, limit: int = 100) -> List[UserRank]:
    return db.query(UserRank).order_by(UserRank.total_score.desc()).limit(limit).all()

def create_or_update_user_rank(db: Session, uid: str, username: str, email: str, score_delta: float = 0, won: bool = False) -> UserRank:
    user_rank = get_user_rank(db, uid)
    
    if not user_rank:
        user_rank = UserRank(
            uid=uid,
            username=username,
            email=email,
            total_score=score_delta,
            games_played=1,
            games_won=1 if won else 0
        )
        db.add(user_rank)
    else:
        user_rank.total_score += score_delta
        user_rank.games_played += 1
        if won:
            user_rank.games_won += 1
        user_rank.username = username  # Update username in case it changed
    
    db.commit()
    db.refresh(user_rank)
    return user_rank

def get_user_rank_position(db: Session, uid: str) -> Optional[int]:
    user_rank = get_user_rank(db, uid)
    if not user_rank:
        return None
    
    # Count how many users have a higher score
    position = db.query(UserRank).filter(UserRank.total_score > user_rank.total_score).count()
    return position + 1  # Add 1 to make it 1-based indexing

def get_all_user_ranks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(UserRank).order_by(desc(UserRank.total_score)).offset(skip).limit(limit).all()