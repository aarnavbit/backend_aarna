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
        desc("score"),
        "duration_ms"
    ).all()
    
    total_unique_players = len(grouped)
    top_score = int(grouped[0].score or 0) if grouped else 0
    total_duration = sum(int(g.duration_ms or 0) for g in grouped) if grouped else 0
    avg_duration = (total_duration / total_unique_players) if total_unique_players > 0 else 0
    
    players = []
    for i, row in enumerate(grouped):
        players.append({
            "rank": i + 1,
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
            "created_at": row.created_at or 0
        })
    
    return {
        "success": True,
        "gameState": game_state.get_state(),
        "stats": {
            "totalPlayers": total_unique_players,
            "highestScore": top_score,
            "avgDurationSec": round(avg_duration / 1000, 1) if avg_duration else 0,
            "total_players": total_unique_players,
            "top_score": top_score,
            "average_duration_ms": round(avg_duration, 2)
        },
        "players": players,
        "entries": players
    }

@router.get("/export-csv", dependencies=[Depends(verify_admin)])
def export_csv(db: Session = Depends(get_db)):
    grouped = db.query(
        func.max(LeaderboardEntry.player_name).label("player_name"),
        func.sum(LeaderboardEntry.score).label("score"),
        func.sum(LeaderboardEntry.duration_ms).label("duration_ms"),
        func.sum(LeaderboardEntry.rounds_completed).label("rounds_completed"),
        func.sum(LeaderboardEntry.matches).label("matches"),
        func.sum(LeaderboardEntry.mismatches).label("mismatches"),
        func.max(LeaderboardEntry.created_at).label("created_at")
    ).group_by(
        func.lower(func.trim(LeaderboardEntry.player_name))
    ).order_by(
        desc("score"),
        "duration_ms"
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Rank", "Player Name", "Score", "Duration (ms)", 
        "Rounds Completed", "Matches", "Mismatches", "Submitted At"
    ])
    
    for i, entry in enumerate(grouped):
        writer.writerow([
            i + 1,
            entry.player_name,
            int(entry.score or 0),
            int(entry.duration_ms or 0),
            int(entry.rounds_completed or 0),
            int(entry.matches or 0),
            int(entry.mismatches or 0),
            entry.created_at or ""
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
