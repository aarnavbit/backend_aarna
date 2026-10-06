from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import secrets
import string
import time

from app.database import get_db
from app.models.ishanya import IshanyaTeam, IshanyaMember
from app.schemas.ishanya import (
    IshanyaRegisterRequest,
    IshanyaPaymentRequest,
    IshanyaMemberUpdateRequest,
    IshanyaAdminStatusRequest,
    IshanyaAdminUpdateTeamRequest,
)
from app.services.auth import get_current_admin
from app.services.email_service import send_status_email
from app.config import settings

router = APIRouter()

EXPECTED_MEMBERS = settings.ISHANYA_MEMBER_COUNT - 1  # leader counts as member #1


def _generate_registration_id(db: Session) -> str:
    charset = string.ascii_uppercase + string.digits
    for _ in range(100):
        code = "ISH-" + "".join(secrets.choice(charset) for _ in range(4))
        existing = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == code).first()
        if not existing:
            return code
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate unique registration ID",
    )


def _team_to_dict(team: IshanyaTeam, members: list, include_whatsapp: bool = False) -> dict:
    result = {
        "registration_id": team.registration_id,
        "team_name": team.team_name,
        "leader_name": team.leader_name,
        "leader_roll_no": getattr(team, "leader_roll_no", "") or "",
        "leader_dept": getattr(team, "leader_dept", "") or "",
        "leader_sec": getattr(team, "leader_sec", "") or "",
        "leader_year": getattr(team, "leader_year", "") or "",
        "leader_email": team.leader_email,
        "leader_phone": team.leader_phone,
        "amount": getattr(team, "amount", 150) or 150,
        "utr_number": team.utr_number,
        "status": team.status,
        "admin_notes": team.admin_notes,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "members": [
            {
                "name": m.name,
                "roll_no": getattr(m, "roll_no", "") or "",
                "department": getattr(m, "department", "") or "",
                "section": getattr(m, "section", "") or "",
                "year": getattr(m, "year", "") or "",
                "email": getattr(m, "email", "") or "",
                "phone": m.phone,
            }
            for m in members
        ],
    }
    if include_whatsapp and team.status == "accepted":
        result["whatsapp_link"] = settings.ISHANYA_WHATSAPP_GROUP_LINK
    return result


# ---------------------------------------------------------------------------
# Public Endpoints
# ---------------------------------------------------------------------------

@router.post("/register")
def register_team(req: IshanyaRegisterRequest, db: Session = Depends(get_db)):
    if not req.team_name.strip():
        raise HTTPException(status_code=400, detail="Team name is required")
    if not req.leader_name.strip() or not req.leader_email.strip() or not req.leader_phone.strip():
        raise HTTPException(status_code=400, detail="Leader name, email, and phone are required")
    if len(req.members) != EXPECTED_MEMBERS:
        raise HTTPException(
            status_code=400,
            detail=f"Exactly {EXPECTED_MEMBERS} additional member(s) required",
        )
    for i, m in enumerate(req.members):
        if not m.name.strip() or not m.phone.strip():
            raise HTTPException(status_code=400, detail=f"Member {i + 1}: name and phone are required")

    reg_id = _generate_registration_id(db)

    try:
        team = IshanyaTeam(
            registration_id=reg_id,
            team_name=req.team_name.strip(),
            leader_name=req.leader_name.strip(),
            leader_roll_no=(req.leader_roll_no or "").strip(),
            leader_dept=(req.leader_dept or "").strip(),
            leader_sec=(req.leader_sec or "").strip(),
            leader_year=(req.leader_year or "").strip(),
            leader_email=req.leader_email.strip(),
            leader_phone=req.leader_phone.strip(),
            amount=req.amount or settings.ISHANYA_REGISTRATION_FEE,
            status="pending",
            created_at=int(time.time() * 1000),
            updated_at=int(time.time() * 1000),
        )
        db.add(team)
        db.flush()

        for m in req.members:
            member = IshanyaMember(
                team_id=team.id,
                name=m.name.strip(),
                roll_no=(m.roll_no or "").strip(),
                department=(m.department or "").strip(),
                section=(m.sec or "").strip(),
                year=(m.year or "").strip(),
                email=(m.email or "").strip(),
                phone=m.phone.strip(),
                created_at=int(time.time() * 1000),
            )
            db.add(member)

        db.commit()
        db.refresh(team)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

    return {
        "success": True,
        "registration_id": reg_id,
        "message": "Team registered successfully! Please complete payment.",
    }


@router.post("/payment")
def submit_payment(req: IshanyaPaymentRequest, db: Session = Depends(get_db)):
    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == req.registration_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if not req.utr_number.strip():
        raise HTTPException(status_code=400, detail="UTR number is required")

    team.utr_number = req.utr_number.strip()
    if req.screenshot_base64:
        team.payment_screenshot = req.screenshot_base64
    team.updated_at = int(time.time() * 1000)

    db.commit()

    return {"success": True, "message": "Payment details submitted successfully"}


@router.get("/status/{registration_id}")
def get_status(registration_id: str, db: Session = Depends(get_db)):
    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == registration_id).first()
    if not team or team.status == "deleted":
        raise HTTPException(status_code=404, detail="Team not found")

    members = db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).all()
    return _team_to_dict(team, members, include_whatsapp=True)


@router.put("/members/{registration_id}")
def update_members(registration_id: str, req: IshanyaMemberUpdateRequest, db: Session = Depends(get_db)):
    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == registration_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.status != "pending":
        raise HTTPException(status_code=400, detail="Members can only be edited when status is pending")
    if len(req.members) != EXPECTED_MEMBERS:
        raise HTTPException(
            status_code=400,
            detail=f"Exactly {EXPECTED_MEMBERS} additional member(s) required",
        )
    for i, m in enumerate(req.members):
        if not m.name.strip() or not m.phone.strip():
            raise HTTPException(status_code=400, detail=f"Member {i + 1}: name and phone are required")

    # Delete existing members and re-create
    db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).delete()
    for m in req.members:
        member = IshanyaMember(
            team_id=team.id,
            name=m.name.strip(),
            roll_no=(m.roll_no or "").strip(),
            department=(m.department or "").strip(),
            section=(m.sec or "").strip(),
            year=(m.year or "").strip(),
            email=(m.email or "").strip(),
            phone=m.phone.strip(),
            created_at=int(time.time() * 1000),
        )
        db.add(member)

    team.updated_at = int(time.time() * 1000)
    db.commit()

    return {"success": True, "message": "Members updated successfully"}


# ---------------------------------------------------------------------------
# Admin Endpoints (JWT protected)
# ---------------------------------------------------------------------------

@router.get("/admin/teams")
def admin_list_teams(current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    teams = db.query(IshanyaTeam).order_by(IshanyaTeam.id.desc()).all()
    result = []
    for team in teams:
        members = db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).all()
        result.append(_team_to_dict(team, members, include_whatsapp=True))
    return {
        "teams": result,
        "count": len(result),
        "whatsapp_group_link": settings.ISHANYA_WHATSAPP_GROUP_LINK,
    }


@router.put("/admin/teams/{registration_id}/status")
def admin_update_status(
    registration_id: str,
    req: IshanyaAdminStatusRequest,
    background_tasks: BackgroundTasks,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if req.status not in ("accepted", "rejected", "pending"):
        raise HTTPException(status_code=400, detail="Status must be 'accepted', 'rejected', or 'pending'")

    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == registration_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team.status = req.status
    if req.notes is not None:
        team.admin_notes = req.notes
    team.updated_at = int(time.time() * 1000)
    db.commit()

    # Dispatch email asynchronously in background tasks ONLY IF ACCEPTED! (Do not send regret/rejection emails)
    if req.status == "accepted":
        background_tasks.add_task(
            send_status_email,
            to=team.leader_email,
            team_name=team.team_name,
            registration_id=team.registration_id,
            status=req.status,
            whatsapp_link=settings.ISHANYA_WHATSAPP_GROUP_LINK,
        )

    return {
        "success": True,
        "message": f"Team {registration_id} has been {req.status}",
        "team": _team_to_dict(team, db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).all(), include_whatsapp=True),
    }


@router.put("/admin/teams/{registration_id}")
def admin_update_team(
    registration_id: str,
    req: IshanyaAdminUpdateTeamRequest,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == registration_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if req.team_name is not None:
        team.team_name = req.team_name.strip()
    if req.leader_name is not None:
        team.leader_name = req.leader_name.strip()
    if req.leader_roll_no is not None:
        team.leader_roll_no = req.leader_roll_no.strip()
    if req.leader_dept is not None:
        team.leader_dept = req.leader_dept.strip()
    if req.leader_sec is not None:
        team.leader_sec = req.leader_sec.strip()
    if req.leader_email is not None:
        team.leader_email = req.leader_email.strip()
    if req.leader_phone is not None:
        team.leader_phone = req.leader_phone.strip()
    if req.amount is not None:
        team.amount = req.amount
    if req.utr_number is not None:
        team.utr_number = req.utr_number.strip()
    if req.status is not None:
        team.status = req.status
    if req.admin_notes is not None:
        team.admin_notes = req.admin_notes

    # Update members if provided
    if req.members is not None:
        db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).delete()
        for m in req.members:
            if m.name.strip():
                new_m = IshanyaMember(
                    team_id=team.id,
                    name=m.name.strip(),
                    roll_no=(m.roll_no or "").strip(),
                    department=(m.department or "").strip(),
                    section=(m.section or m.sec or "").strip(),
                    email=(m.email or "").strip(),
                    phone=(m.phone or "").strip(),
                    created_at=int(time.time() * 1000),
                )
                db.add(new_m)

    team.updated_at = int(time.time() * 1000)
    db.commit()

    members = db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).all()
    return {
        "success": True,
        "message": f"Team {registration_id} updated successfully",
        "team": _team_to_dict(team, members, include_whatsapp=True),
    }


@router.delete("/admin/teams/trash/purge")
def admin_purge_trash(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    deleted_teams = db.query(IshanyaTeam).filter(IshanyaTeam.status == "deleted").all()
    count = len(deleted_teams)
    for t in deleted_teams:
        db.query(IshanyaMember).filter(IshanyaMember.team_id == t.id).delete()
        db.query(IshanyaTeam).filter(IshanyaTeam.id == t.id).delete()
    db.commit()

    return {"success": True, "message": f"Permanently removed {count} team(s) from trash", "purged_count": count}


@router.delete("/admin/teams/{registration_id}")
def admin_soft_delete_team(
    registration_id: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == registration_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team.status = "deleted"
    team.updated_at = int(time.time() * 1000)
    db.commit()

    return {"success": True, "message": f"Team {registration_id} moved to trash"}


@router.post("/admin/teams/{registration_id}/restore")
def admin_restore_team(
    registration_id: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == registration_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team.status = "pending"
    team.updated_at = int(time.time() * 1000)
    db.commit()

    members = db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).all()
    return {
        "success": True,
        "message": f"Team {registration_id} restored to pending",
        "team": _team_to_dict(team, members, include_whatsapp=True),
    }


@router.delete("/admin/teams/{registration_id}/permanent")
def admin_permanent_delete_team(
    registration_id: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == registration_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).delete()
    db.query(IshanyaTeam).filter(IshanyaTeam.id == team.id).delete()
    db.commit()

    return {"success": True, "message": f"Team {registration_id} permanently removed from database"}


@router.get("/admin/teams/{registration_id}/screenshot")
def admin_get_screenshot(
    registration_id: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == registration_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"screenshot": team.payment_screenshot}


@router.post("/admin/init-db")
def admin_init_db(
    current_admin=Depends(get_current_admin),
):
    try:
        from app.database import engine, Base
        Base.metadata.create_all(bind=engine)
        return {"success": True, "message": "Database tables verified/created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")
