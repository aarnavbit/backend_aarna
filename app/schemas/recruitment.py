from pydantic import BaseModel, Field
from typing import Optional, Union

class RecruitmentAdminLogin(BaseModel):
    rollnumber: Optional[str] = None
    rollNumber: Optional[str] = None
    password: str

    @property
    def clean_rollnumber(self) -> str:
        val = self.rollnumber or self.rollNumber or ""
        return val.strip().upper()

class CreateSubAdminSchema(BaseModel):
    rollnumber: str
    password: str
    assigned_department: Optional[str] = None
    assigned_section: Optional[str] = None

class ApplicationSubmissionSchema(BaseModel):
    fullname: Optional[str] = None
    fullName: Optional[str] = None
    emailaddress: Optional[str] = None
    collegeEmail: Optional[str] = None
    rollnumber: Optional[str] = None
    rollNumber: Optional[str] = None
    mobilenumber: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    academicDepartment: Optional[str] = None
    section: Optional[str] = None
    year: Optional[Union[str, int]] = None
    portfolio: Optional[str] = None
    primaryPortfolio: Optional[str] = None
    secondaryPortfolio: Optional[str] = None
    knowaboutaarna: Optional[str] = None
    experience: Optional[str] = None
    whyjoinaarna: Optional[str] = None
    motivation: Optional[str] = None
    skills: Optional[str] = None
    previousclub: Optional[str] = None
    currentclub: Optional[str] = None
    leadershiprating: Optional[Union[int, str]] = 5
