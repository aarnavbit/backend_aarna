from sqlalchemy import Column, String, Text, BigInteger
import uuid
from app.database import Base

class GameSession(Base):
    __tablename__ = "game_sessions"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    player_name = Column(String(50), nullable=False)
    config_json = Column(Text, nullable=False)
    status = Column(String(20), default='active')
    created_at = Column(BigInteger, nullable=False)
    expires_at = Column(BigInteger, nullable=False, index=True)
