from pydantic import BaseModel
from typing import Dict, Any, Optional

class GameStartRequest(BaseModel):
    player_name: str

class GameScoreRequest(BaseModel):
    session_id: str
    duration_ms: int
    rounds_completed: int
    matches: int
    mismatches: int

class AdminLoginRequest(BaseModel):
    password: str
