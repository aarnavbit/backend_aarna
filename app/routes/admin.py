from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import csv
import io

from app.config import settings
from app.database import get_db
from app.models.session import GameSession
from app.models.leaderboard import LeaderboardEntry
from app.schemas.game import AdminLoginRequest
from app.services.game_state import game_state
from app.socketio_app import broadcast_game_started, broadcast_game_ended, broadcast_lobby_reset

router = APIRouter()

def verify_admin(x_admin_password: str = Header(...)):
    if x_admin_password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    return True

@router.post("/login")
def login(req: AdminLoginRequest):
    if req.password == settings.ADMIN_PASSWORD:
        return {
            "success": True,
            "gameState": game_state.get_state()
        }
    raise HTTPException(status_code=401, detail="Invalid admin password")

@router.post("/game/start", dependencies=[Depends(verify_admin)])
async def admin_start_game():
    state = game_state.start_round()
    await broadcast_game_started()
    return {
        "success": True,
        "gameState": state
    }

@router.post("/game/stop", dependencies=[Depends(verify_admin)])
async def admin_stop_game():
    state = game_state.stop_round()
    await broadcast_game_ended()
    return {
        "success": True,
        "gameState": state
    }

@router.post("/game/reset-lobby", dependencies=[Depends(verify_admin)])
async def admin_reset_lobby():
    state = game_state.reset_lobby()
    await broadcast_lobby_reset()
    return {
        "success": True,
        "gameState": state
    }

@router.get("/scores", dependencies=[Depends(verify_admin)])
def admin_get_scores(db: Session = Depends(get_db)):
    entries = db.query(LeaderboardEntry).order_by(
        desc(LeaderboardEntry.score),
        LeaderboardEntry.duration_ms
    ).all()
    
    total_players = db.query(LeaderboardEntry).count()
    top_score = db.query(func.max(LeaderboardEntry.score)).scalar() or 0
    avg_duration = db.query(func.avg(LeaderboardEntry.duration_ms)).scalar() or 0
    
    players = []
    for i, entry in enumerate(entries):
        players.append({
            "rank": i + 1,
            "sessionId": entry.session_id,
            "playerName": entry.player_name,
            "score": entry.score,
            "durationMs": entry.duration_ms,
            "roundsCompleted": entry.rounds_completed,
            "matches": entry.matches,
            "mismatches": entry.mismatches,
            "createdAt": entry.created_at
        })
    
    return {
        "success": True,
        "gameState": game_state.get_state(),
        "stats": {
            "totalPlayers": total_players,
            "highestScore": top_score,
            "avgDurationSec": round(avg_duration / 1000, 1) if avg_duration else 0,
            "total_players": total_players,
            "top_score": top_score,
            "average_duration_ms": round(avg_duration, 2)
        },
        "players": players,
        "entries": entries
    }

@router.get("/export-csv", dependencies=[Depends(verify_admin)])
def export_csv(db: Session = Depends(get_db)):
    entries = db.query(LeaderboardEntry).order_by(
        desc(LeaderboardEntry.score),
        LeaderboardEntry.duration_ms
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Rank", "Player Name", "Score", "Duration (ms)", 
        "Rounds Completed", "Matches", "Mismatches", "Submitted At"
    ])
    
    for i, entry in enumerate(entries):
        writer.writerow([
            i + 1,
            entry.player_name,
            entry.score,
            entry.duration_ms,
            entry.rounds_completed,
            entry.matches,
            entry.mismatches,
            entry.created_at
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leaderboard.csv"}
    )

@router.post("/reset", dependencies=[Depends(verify_admin)])
async def reset_data(db: Session = Depends(get_db)):
    db.query(LeaderboardEntry).delete()
    db.query(GameSession).delete()
    db.commit()
    
    state = game_state.reset_lobby()
    await broadcast_lobby_reset()
    
    return {
        "success": True,
        "message": "All data cleared successfully",
        "gameState": state
    }
