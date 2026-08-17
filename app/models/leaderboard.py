from sqlalchemy import Column, Integer, String, BigInteger, Index
from app.database import Base

class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False)
    player_name = Column(String(50), nullable=False)
    score = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    rounds_completed = Column(Integer, nullable=False)
    matches = Column(Integer, nullable=False)
    mismatches = Column(Integer, nullable=False)
    created_at = Column(BigInteger, nullable=False)

    __table_args__ = (
        Index('ix_score_duration', 'score', 'duration_ms', unique=False),
    )
