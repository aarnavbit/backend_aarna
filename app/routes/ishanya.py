from fastapi import APIRouter, Depends, HTTPException, status
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
        "leader_email": team.leader_email,
        "leader_phone": team.leader_phone,
        "utr_number": team.utr_number,
        "status": team.status,
        "admin_notes": team.admin_notes,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "members": [{"name": m.name, "phone": m.phone} for m in members],
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
            leader_email=req.leader_email.strip(),
            leader_phone=req.leader_phone.strip(),
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
    if not team:
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
        result.append(_team_to_dict(team, members))
    return {"teams": result, "count": len(result)}


@router.put("/admin/teams/{registration_id}/status")
def admin_update_status(
    registration_id: str,
    req: IshanyaAdminStatusRequest,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if req.status not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'rejected'")

    team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == registration_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team.status = req.status
    if req.notes is not None:
        team.admin_notes = req.notes
    team.updated_at = int(time.time() * 1000)
    db.commit()

    # Send status email (fire-and-forget)
    try:
        send_status_email(
            to=team.leader_email,
            team_name=team.team_name,
            registration_id=team.registration_id,
            status=req.status,
            whatsapp_link=settings.ISHANYA_WHATSAPP_GROUP_LINK,
        )
    except Exception as e:
        print(f"[ISHANYA] Email send failed: {e}")

    return {"success": True, "message": f"Team {registration_id} has been {req.status}"}


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
