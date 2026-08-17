from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
import time
import uuid
import json

from app.database import get_db
from app.models.session import GameSession
from app.models.leaderboard import LeaderboardEntry
from app.schemas.game import GameStartRequest, GameScoreRequest
from app.schemas.leaderboard import LeaderboardEntryResponse
from app.services.game_state import game_state
from app.services.score_service import ScoreService
from app.socketio_app import broadcast_leaderboard_update

router = APIRouter()

@router.get("/status")
def get_status():
    return game_state.get_state()

@router.post("/start")
def start_game(req: GameStartRequest, db: Session = Depends(get_db)):
    state = game_state.get_state()
    if state["status"] != 'playing':
        raise HTTPException(status_code=400, detail="Game is not currently active")
        
    session_id = str(uuid.uuid4())
    now_ms = int(time.time() * 1000)
    
    # Store minimal config for the game, as requested
    db_session = GameSession(
        session_id=session_id,
        player_name=req.player_name,
        config_json=json.dumps({"round_id": state["round_id"]}),
        status='active',
        created_at=now_ms,
        expires_at=now_ms + 3600000 # 1 hour
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return {
        "session_id": db_session.session_id,
        "player_name": db_session.player_name,
        "global_start_time": state["start_time"],
        "status": state["status"]
    }

@router.post("/score")
async def submit_score(req: GameScoreRequest, db: Session = Depends(get_db)):
    # Verify session exists
    db_session = db.query(GameSession).filter(GameSession.session_id == req.session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    try:
        score_data = ScoreService.validate_and_score(
            matches=req.matches,
            mismatches=req.mismatches,
            rounds_completed=req.rounds_completed,
            client_duration_ms=req.duration_ms
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Check if already submitted
    existing_entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.session_id == req.session_id).first()
    
    if score_data["round_ended"]:
        # Only return score, don't save to competitive leaderboard
        return {
            "message": "Round ended before submission, score not saved to leaderboard.",
            "score": score_data["score"],
            "saved": False
        }
        
    if existing_entry:
        # Update existing
        existing_entry.score = score_data["score"]
        existing_entry.duration_ms = req.duration_ms
        existing_entry.rounds_completed = req.rounds_completed
        existing_entry.matches = req.matches
        existing_entry.mismatches = req.mismatches
    else:
        # Insert new
        new_entry = LeaderboardEntry(
            session_id=req.session_id,
            player_name=db_session.player_name,
            score=score_data["score"],
            duration_ms=req.duration_ms,
            rounds_completed=req.rounds_completed,
            matches=req.matches,
            mismatches=req.mismatches,
            created_at=int(time.time() * 1000)
        )
        db.add(new_entry)
        
    db_session.status = 'completed'
    db.commit()
    
    # Broadcast to all clients to update leaderboard
    await broadcast_leaderboard_update()
    
    return {
        "message": "Score saved successfully",
        "score": score_data["score"],
        "saved": True
    }

@router.get("/session/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(GameSession).filter(GameSession.session_id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Get entry if exists
    entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.session_id == session_id).first()
    
    rank = None
    if entry:
        # Calculate rank based on composite index order (score DESC, duration_ms ASC)
        higher_scores_count = db.query(LeaderboardEntry).filter(
            (LeaderboardEntry.score > entry.score) |
            ((LeaderboardEntry.score == entry.score) & (LeaderboardEntry.duration_ms < entry.duration_ms))
        ).count()
        rank = higher_scores_count + 1
        
    return {
        "session": {
            "session_id": db_session.session_id,
            "player_name": db_session.player_name,
            "status": db_session.status
        },
        "score_data": entry,
        "rank": rank
    }

@router.get("/leaderboard")
def get_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    entries = db.query(LeaderboardEntry).order_by(
        desc(LeaderboardEntry.score),
        LeaderboardEntry.duration_ms
    ).limit(limit).all()
    
    return entries

