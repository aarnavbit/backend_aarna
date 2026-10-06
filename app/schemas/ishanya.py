from pydantic import BaseModel
from typing import List, Optional


class IshanyaMemberSchema(BaseModel):
    name: str
    roll_no: Optional[str] = ""
    department: Optional[str] = ""
    sec: Optional[str] = ""
    section: Optional[str] = ""
    year: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""


class IshanyaRegisterRequest(BaseModel):
    team_name: str
    leader_name: str
    leader_roll_no: Optional[str] = ""
    leader_dept: Optional[str] = ""
    leader_sec: Optional[str] = ""
    leader_year: Optional[str] = ""
    leader_email: str
    leader_phone: str
    amount: Optional[int] = 150
    members: List[IshanyaMemberSchema]


class IshanyaPaymentRequest(BaseModel):
    registration_id: str
    utr_number: str
    screenshot_base64: Optional[str] = None


class IshanyaMemberUpdateRequest(BaseModel):
    members: List[IshanyaMemberSchema]


class IshanyaAdminStatusRequest(BaseModel):
    status: str
    notes: Optional[str] = None


class IshanyaAdminUpdateTeamRequest(BaseModel):
    team_name: Optional[str] = None
    leader_name: Optional[str] = None
    leader_roll_no: Optional[str] = None
    leader_dept: Optional[str] = None
    leader_sec: Optional[str] = None
    leader_email: Optional[str] = None
    leader_phone: Optional[str] = None
    amount: Optional[int] = None
    utr_number: Optional[str] = None
    status: Optional[str] = None
    admin_notes: Optional[str] = None
    members: Optional[List[IshanyaMemberSchema]] = None
