from pydantic import BaseModel
from typing import List

class LeaderboardEntryResponse(BaseModel):
    player_name: str
    score: int
    duration_ms: int
    rounds_completed: int
    matches: int
    mismatches: int

    class Config:
        from_attributes = True
