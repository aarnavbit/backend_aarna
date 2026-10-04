from pydantic import BaseModel
from typing import List, Optional


class IshanyaMemberSchema(BaseModel):
    name: str
    roll_no: Optional[str] = ""
    department: Optional[str] = ""
    sec: Optional[str] = ""
    email: Optional[str] = ""
    phone: str


class IshanyaRegisterRequest(BaseModel):
    team_name: str
    leader_name: str
    leader_roll_no: Optional[str] = ""
    leader_dept: Optional[str] = ""
    leader_sec: Optional[str] = ""
    leader_email: str
    leader_phone: str
    amount: Optional[int] = 300
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
