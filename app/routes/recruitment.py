from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import time

from app.database import get_db
from app.models.registration import Admin, Registration
from app.schemas.recruitment import RecruitmentAdminLogin, CreateSubAdminSchema, ApplicationSubmissionSchema
from app.services.auth import verify_password, hash_password, generate_admin_token, get_current_admin
from app.config import settings

router = APIRouter()

# ---------------------------------------------------------------------------
# Admin Authentication & Management Routes
# ---------------------------------------------------------------------------

@router.post("/admin/login")
@router.post("/admin/session")
def admin_login(req: RecruitmentAdminLogin, db: Session = Depends(get_db)):
    roll = req.clean_rollnumber
    if not roll or not req.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roll number and password are required"
        )

    admin = db.query(Admin).filter(Admin.rollnumber == roll).first()
    if not admin or not verify_password(req.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = generate_admin_token(admin.id, admin.rollnumber, admin.role)
    return {
        "token": token,
        "admin": {
            "id": admin.id,
            "rollnumber": admin.rollnumber,
            "role": admin.role,
            "assigned_department": admin.assigned_department,
            "assigned_section": admin.assigned_section
        }
    }

@router.get("/admin/me")
def get_admin_me(current_admin: Admin = Depends(get_current_admin)):
    return {
        "admin": {
            "id": current_admin.id,
            "rollnumber": current_admin.rollnumber,
            "role": current_admin.role,
            "assigned_department": current_admin.assigned_department,
            "assigned_section": current_admin.assigned_section
        }
    }

@router.post("/admin/create", status_code=status.HTTP_201_CREATED)
def create_subadmin(
    req: CreateSubAdminSchema,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if current_admin.role != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can create sub-admins"
        )

    rollnumber = req.rollnumber.strip().upper()
    if not rollnumber or not req.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roll number and password are required"
        )

    existing = db.query(Admin).filter(Admin.rollnumber == rollnumber).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An admin with this roll number already exists"
        )

    new_admin = Admin(
        rollnumber=rollnumber,
        password_hash=hash_password(req.password),
        role='subadmin',
        assigned_department=req.assigned_department.strip() if req.assigned_department else None,
        assigned_section=req.assigned_section.strip() if req.assigned_section else None,
        created_at=int(time.time() * 1000)
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {"report": "Sub-Admin created successfully!", "success": True}

@router.get("/admin/subadmins")
def list_subadmins(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if current_admin.role != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can view sub-admins list"
        )

    subadmins = db.query(Admin).filter(Admin.role == 'subadmin').all()
    result = []
    for sa in subadmins:
        result.append({
            "id": sa.id,
            "rollnumber": sa.rollnumber,
            "assigned_department": sa.assigned_department or "All",
            "assigned_section": sa.assigned_section or "All"
        })
    return {"subadmins": result}

@router.get("/admin/applicants")
@router.get("/admin/applications")
def list_applicants(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Registration)

    if current_admin.role == 'subadmin':
        if current_admin.assigned_department and current_admin.assigned_department.lower() != 'all':
            query = query.filter(Registration.department.ilike(f"%{current_admin.assigned_department}%"))
        if current_admin.assigned_section and current_admin.assigned_section.lower() != 'all':
            query = query.filter(Registration.section.ilike(f"%{current_admin.assigned_section}%"))

    applicants = query.order_by(Registration.id.desc()).all()
    result = []
    for app in applicants:
        result.append({
            "id": app.id,
            "fullname": app.fullname,
            "emailaddress": app.emailaddress,
            "rollnumber": app.rollnumber,
            "mobilenumber": app.mobilenumber,
            "department": app.department,
            "section": app.section,
            "year": app.year,
            "portfolio": app.portfolio,
            "knowaboutaarna": app.knowaboutaarna,
            "whyjoinaarna": app.whyjoinaarna,
            "skills": app.skills,
            "previousclub": app.previousclub or "N/A",
            "currentclub": app.currentclub or "N/A",
            "leadershiprating": app.leadershiprating,
            "created_at": app.created_at
        })

    return {
        "applicants": result,
        "items": result,
        "count": len(result)
    }

@router.get("/admin/sync-status")
def get_sync_status(current_admin: Admin = Depends(get_current_admin)):
    return {
        "status": "synced",
        "synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

# ---------------------------------------------------------------------------
# Applicant Registration Routes
# ---------------------------------------------------------------------------

@router.post("/applications")
@router.post("/userregistration/")
def register_applicant(req: ApplicationSubmissionSchema, db: Session = Depends(get_db)):
    fullname = (req.fullname or req.fullName or "").strip()
    emailaddress = (req.emailaddress or req.collegeEmail or "").strip()
    rollnumber = (req.rollnumber or req.rollNumber or "").strip().upper()
    mobilenumber = (req.mobilenumber or req.phone or "").strip()
    department = (req.department or req.academicDepartment or "").strip()
    section = (req.section or "").strip()
    year = str(req.year or "").strip()

    primary_pref = req.portfolio or req.primaryPortfolio or ""
    secondary_pref = req.secondaryPortfolio or ""
    portfolio = f"{primary_pref} / {secondary_pref}".strip(" /") if secondary_pref else primary_pref
    if not portfolio:
        portfolio = "General"

    knowaboutaarna = (req.knowaboutaarna or req.experience or "N/A").strip()
    whyjoinaarna = (req.whyjoinaarna or req.motivation or "N/A").strip()
    skills = (req.skills or "N/A").strip()

    try:
        leadership_rating = int(req.leadershiprating or 5)
    except (ValueError, TypeError):
        leadership_rating = 5

    previous_club = req.previousclub or ""
    current_club = req.currentclub or ""

    if not fullname or not emailaddress or not rollnumber:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name, email address, and roll number are required."
        )

    try:
        new_registration = Registration(
            fullname=fullname,
            emailaddress=emailaddress,
            rollnumber=rollnumber,
            mobilenumber=mobilenumber,
            department=department,
            section=section,
            year=year,
            portfolio=portfolio,
            knowaboutaarna=knowaboutaarna,
            whyjoinaarna=whyjoinaarna,
            skills=skills,
            previousclub=previous_club,
            currentclub=current_club,
            leadershiprating=leadership_rating,
            created_at=int(time.time() * 1000)
        )
        db.add(new_registration)
        db.commit()
        db.refresh(new_registration)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during registration: {str(e)}"
        )

    return {
        "success": True,
        "report": "Registration successful! Please join our WhatsApp group.",
        "message": "Application submitted successfully!",
        "whatsapplink": settings.WHATSAPP_GROUP_LINK,
        "application": {
            "id": new_registration.id,
            "fullname": new_registration.fullname,
            "rollnumber": new_registration.rollnumber
        }
    }
