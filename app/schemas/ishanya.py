from pydantic import BaseModel
from typing import List, Optional


class IshanyaMemberSchema(BaseModel):
    name: str
    phone: str


class IshanyaRegisterRequest(BaseModel):
    team_name: str
    leader_name: str
    leader_email: str
    leader_phone: str
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
