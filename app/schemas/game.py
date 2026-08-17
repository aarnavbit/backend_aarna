from pydantic import BaseModel
from typing import Dict, Any, Optional

class GameStartRequest(BaseModel):
    player_name: Optional[str] = None
    playerName: Optional[str] = None

    @property
    def name(self) -> str:
        return (self.playerName or self.player_name or "Player").strip()

class GameScoreRequest(BaseModel):
    session_id: Optional[str] = None
    sessionId: Optional[str] = None
    player_name: Optional[str] = None
    playerName: Optional[str] = None
    duration_ms: Optional[int] = None
    durationMs: Optional[int] = None
    rounds_completed: Optional[int] = None
    roundsCompleted: Optional[int] = None
    matches: Optional[int] = None
    mismatches: Optional[int] = None
    actions: Optional[Dict[str, Any]] = None

class AdminLoginRequest(BaseModel):
    password: str
