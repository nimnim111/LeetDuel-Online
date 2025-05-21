from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from ..crud import get_top_players, get_user_rank, get_user_rank_position
from ..dataclass import LadderEntry, LadderResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/ladder", response_model=LadderResponse)
def get_ladder(limit: int = 100, db: Session = Depends(get_db)):
    players = get_top_players(db, limit)
    entries = [
        LadderEntry(
            rank=i+1,
            username=player.username,
            total_score=player.total_score,
            games_played=player.games_played,
            games_won=player.games_won
        )
        for i, player in enumerate(players)
    ]
    return LadderResponse(entries=entries)

@router.get("/ladder/user/{uid}")
def get_user_ladder_info(uid: str, db: Session = Depends(get_db)):
    user_rank = get_user_rank(db, uid)
    if not user_rank:
        raise HTTPException(status_code=404, detail="User not found")
    
    position = get_user_rank_position(db, uid)
    return {
        "rank": position,
        "username": user_rank.username,
        "total_score": user_rank.total_score,
        "games_played": user_rank.games_played,
        "games_won": user_rank.games_won
    } 