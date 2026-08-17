from sqlalchemy import Column, Integer, String, Text, BigInteger
from app.database import Base
import time

class Admin(Base):
    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True, index=True)
    rollnumber = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='subadmin')  # 'superadmin' | 'subadmin'
    assigned_department = Column(String(100), nullable=True)
    assigned_section = Column(String(20), nullable=True)
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000), nullable=False)

class Registration(Base):
    __tablename__ = 'registration'

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(150), nullable=False)
    emailaddress = Column(String(150), nullable=False)
    rollnumber = Column(String(50), index=True, nullable=False)
    mobilenumber = Column(String(20), nullable=False)
    department = Column(String(100), nullable=False)
    section = Column(String(20), nullable=False)
    year = Column(String(20), nullable=False)
    portfolio = Column(String(150), nullable=False)
    knowaboutaarna = Column(Text, nullable=False)
    whyjoinaarna = Column(Text, nullable=False)
    skills = Column(Text, nullable=False)
    previousclub = Column(Text, nullable=True)
    currentclub = Column(Text, nullable=True)
    leadershiprating = Column(Integer, nullable=False, default=5)
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000), nullable=False)
