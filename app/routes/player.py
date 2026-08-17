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
    state = game_state.get_state()
    return {
        "status": state["status"],
        "gameState": state,
        **state
    }

@router.post("/start")
def start_game(req: GameStartRequest, db: Session = Depends(get_db)):
    state = game_state.get_state()
    session_id = str(uuid.uuid4())
    now_ms = int(time.time() * 1000)
    player_name = req.name
    
    db_session = GameSession(
        session_id=session_id,
        player_name=player_name,
        config_json=json.dumps({"round_id": state["round_id"]}),
        status='active',
        created_at=now_ms,
        expires_at=now_ms + 3600000 # 1 hour
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return {
        "sessionId": db_session.session_id,
        "session_id": db_session.session_id,
        "playerName": db_session.player_name,
        "player_name": db_session.player_name,
        "globalStartTime": state["start_time"],
        "global_start_time": state["start_time"],
        "status": state["status"],
        "inLobby": state["status"] == 'waiting',
        "gameState": state
    }

@router.post("/score")
async def submit_score(req: GameScoreRequest, db: Session = Depends(get_db)):
    session_id = req.sessionId or req.session_id
    actions = req.actions or {}
    
    matches = req.matches if req.matches is not None else actions.get("matches", 0)
    mismatches = req.mismatches if req.mismatches is not None else actions.get("mismatches", 0)
    rounds_completed = req.roundsCompleted if req.roundsCompleted is not None else (req.rounds_completed if req.rounds_completed is not None else actions.get("roundsCompleted", 3))
    duration_ms = req.durationMs if req.durationMs is not None else (req.duration_ms if req.duration_ms is not None else actions.get("durationMs", 0))
    player_name = req.playerName or req.player_name or "Player"
    
    if not session_id:
        session_id = str(uuid.uuid4())
        
    db_session = db.query(GameSession).filter(GameSession.session_id == session_id).first()
    if not db_session:
        now_ms = int(time.time() * 1000)
        db_session = GameSession(
            session_id=session_id,
            player_name=player_name,
            config_json=json.dumps({}),
            status='completed',
            created_at=now_ms,
            expires_at=now_ms + 3600000
        )
        db.add(db_session)
        db.commit()
        
    try:
        score_data = ScoreService.validate_and_score(
            matches=matches,
            mismatches=mismatches,
            rounds_completed=rounds_completed,
            client_duration_ms=duration_ms
        )
    except ValueError:
        score_data = {
            "score": ScoreService.calculate_score(matches, mismatches, rounds_completed, duration_ms),
            "round_ended": False
        }
        
    existing_entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.session_id == session_id).first()
    
    if score_data.get("round_ended"):
        return {
            "message": "Round ended before submission, score not saved to leaderboard.",
            "score": score_data["score"],
            "saved": False,
            "roundEnded": True
        }
        
    if existing_entry:
        existing_entry.score = score_data["score"]
        existing_entry.duration_ms = duration_ms
        existing_entry.rounds_completed = rounds_completed
        existing_entry.matches = matches
        existing_entry.mismatches = mismatches
    else:
        new_entry = LeaderboardEntry(
            session_id=session_id,
            player_name=db_session.player_name or player_name,
            score=score_data["score"],
            duration_ms=duration_ms,
            rounds_completed=rounds_completed,
            matches=matches,
            mismatches=mismatches,
            created_at=int(time.time() * 1000)
        )
        db.add(new_entry)
        
    db_session.status = 'completed'
    db.commit()
    
    await broadcast_leaderboard_update()
    
    return {
        "message": "Score saved successfully",
        "score": score_data["score"],
        "saved": True,
        "roundEnded": False
    }

@router.get("/session/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(GameSession).filter(GameSession.session_id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.session_id == session_id).first()
    
    rank = None
    if entry:
        faster_count = db.query(LeaderboardEntry).filter(
            (LeaderboardEntry.duration_ms < entry.duration_ms) |
            ((LeaderboardEntry.duration_ms == entry.duration_ms) & (LeaderboardEntry.score > entry.score))
        ).count()
        rank = faster_count + 1
        
    return {
        "session": {
            "session_id": db_session.session_id,
            "sessionId": db_session.session_id,
            "player_name": db_session.player_name,
            "playerName": db_session.player_name,
            "status": db_session.status
        },
        "score_data": entry,
        "rank": rank
    }

@router.get("/leaderboard")
def get_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    grouped = db.query(
        func.max(LeaderboardEntry.player_name).label("player_name"),
        func.sum(LeaderboardEntry.score).label("score"),
        func.sum(LeaderboardEntry.duration_ms).label("duration_ms"),
        func.sum(LeaderboardEntry.rounds_completed).label("rounds_completed"),
        func.sum(LeaderboardEntry.matches).label("matches"),
        func.sum(LeaderboardEntry.mismatches).label("mismatches"),
        func.max(LeaderboardEntry.created_at).label("created_at"),
        func.max(LeaderboardEntry.session_id).label("session_id"),
        func.min(LeaderboardEntry.id).label("id")
    ).group_by(
        func.lower(func.trim(LeaderboardEntry.player_name))
    ).order_by(
        "duration_ms",
        desc("score")
    ).limit(limit).all()
    
    results = []
    for row in grouped:
        results.append({
            "id": row.id,
            "sessionId": row.session_id,
            "session_id": row.session_id,
            "playerName": row.player_name,
            "player_name": row.player_name,
            "score": int(row.score or 0),
            "durationMs": int(row.duration_ms or 0),
            "duration_ms": int(row.duration_ms or 0),
            "roundsCompleted": int(row.rounds_completed or 0),
            "rounds_completed": int(row.rounds_completed or 0),
            "matches": int(row.matches or 0),
            "mismatches": int(row.mismatches or 0),
            "createdAt": row.created_at or 0,
            "created_at": row.created_at or 0,
        })
    
    return results
