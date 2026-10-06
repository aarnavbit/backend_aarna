from sqlalchemy import Column, Integer, String, Text, BigInteger
from app.database import Base
import time


class IshanyaTeam(Base):
    __tablename__ = 'ishanya_team'

    id = Column(Integer, primary_key=True, index=True)
    registration_id = Column(String(20), unique=True, index=True, nullable=False)
    team_name = Column(String(150), unique=True, index=True, nullable=False)
    leader_name = Column(String(150), nullable=False)
    leader_roll_no = Column(String(50), nullable=True)
    leader_dept = Column(String(100), nullable=True)
    leader_sec = Column(String(20), nullable=True)
    leader_year = Column(String(10), nullable=True)  # nullable: existing rows unaffected
    leader_email = Column(String(150), nullable=False)
    leader_phone = Column(String(20), nullable=False)
    amount = Column(Integer, default=150, nullable=False)
    utr_number = Column(String(100), unique=True, index=True, nullable=True)
    payment_screenshot = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='pending')  # 'pending' | 'accepted' | 'rejected'
    admin_notes = Column(Text, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000), nullable=False)
    updated_at = Column(BigInteger, default=lambda: int(time.time() * 1000), onupdate=lambda: int(time.time() * 1000), nullable=False)


class IshanyaMember(Base):
    __tablename__ = 'ishanya_member'

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, nullable=False)  # soft FK to ishanya_team.id
    name = Column(String(150), nullable=False)
    roll_no = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    section = Column(String(20), nullable=True)
    year = Column(String(10), nullable=True)  # nullable: existing rows unaffected
    email = Column(String(150), nullable=True)
    phone = Column(String(20), nullable=False)
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000), nullable=False)
