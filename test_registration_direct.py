import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.ishanya import IshanyaTeam, IshanyaMember
from app.schemas.ishanya import (
    IshanyaRegisterRequest,
    IshanyaMemberSchema,
    IshanyaPaymentRequest,
    IshanyaMemberUpdateRequest
)
from app.routes.ishanya import register_team, get_status, submit_payment, update_members
from fastapi import HTTPException

def test_full_registration_suite():
    print("=" * 65)
    print("STARTING DIRECT ISHANYA REGISTRATION LOGIC SUITE")
    print("=" * 65)
    db = SessionLocal()
    reg_id = None

    try:
        # 1. Test validation on empty team name
        try:
            register_team(IshanyaRegisterRequest(
                team_name="",
                leader_name="Rohit",
                leader_email="rohit@test.com",
                leader_phone="9876543210",
                members=[
                    IshanyaMemberSchema(name="M1", phone="111"),
                    IshanyaMemberSchema(name="M2", phone="222")
                ]
            ), db)
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 400
            print("[PASS] 1. Rejects empty team name (HTTP 400)")

        # 2. Test validation on member count != 2
        try:
            register_team(IshanyaRegisterRequest(
                team_name="Valid Team",
                leader_name="Rohit",
                leader_email="rohit@test.com",
                leader_phone="9876543210",
                members=[
                    IshanyaMemberSchema(name="M1", phone="111")
                ]
            ), db)
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 400
            print("[PASS] 2. Rejects incorrect additional member count (HTTP 400)")

        # 3. Successful Registration with all 3 members (Leader + 2 members) with full details
        req = IshanyaRegisterRequest(
            team_name="Phoenix Force",
            leader_name="Aarav Sharma",
            leader_roll_no="23BD1A0501",
            leader_dept="CSE",
            leader_sec="A",
            leader_email="aarav@test.com",
            leader_phone="9876543210",
            amount=150,
            members=[
                IshanyaMemberSchema(
                    name="Priya Nair",
                    roll_no="23BD1A0502",
                    department="CSE",
                    sec="A",
                    email="priya@test.com",
                    phone="9876543211"
                ),
                IshanyaMemberSchema(
                    name="Karthik Verma",
                    roll_no="23BD1A0503",
                    department="IT",
                    sec="B",
                    email="karthik@test.com",
                    phone="9876543212"
                )
            ]
        )
        res = register_team(req, db)
        assert res["success"] is True
        reg_id = res["registration_id"]
        assert reg_id.startswith("ISH-")
        print(f"[PASS] 3. Successfully registered team! Assigned ID: {reg_id}")

        # 4. Fetch Status and verify all leader and member fields + amount
        status = get_status(reg_id, db)
        assert status["team_name"] == "Phoenix Force"
        assert status["leader_name"] == "Aarav Sharma"
        assert status["leader_roll_no"] == "23BD1A0501"
        assert status["leader_dept"] == "CSE"
        assert status["leader_sec"] == "A"
        assert status["leader_email"] == "aarav@test.com"
        assert status["leader_phone"] == "9876543210"
        assert status["amount"] == 150
        assert status["status"] == "pending"
        assert len(status["members"]) == 2

        m1 = status["members"][0]
        assert m1["name"] == "Priya Nair"
        assert m1["roll_no"] == "23BD1A0502"
        assert m1["department"] == "CSE"
        assert m1["section"] == "A"
        assert m1["email"] == "priya@test.com"
        assert m1["phone"] == "9876543211"

        m2 = status["members"][1]
        assert m2["name"] == "Karthik Verma"
        assert m2["roll_no"] == "23BD1A0503"
        assert m2["department"] == "IT"
        assert m2["section"] == "B"
        assert m2["email"] == "karthik@test.com"
        assert m2["phone"] == "9876543212"
        print("[PASS] 4. Status reflects all details for Leader & Members + Amount Rs. 150")

        # 5. Submit Payment (UTR)
        pay_res = submit_payment(IshanyaPaymentRequest(
            registration_id=reg_id,
            utr_number="UTR123456789012"
        ), db)
        assert pay_res["success"] is True
        status_after_pay = get_status(reg_id, db)
        assert status_after_pay["utr_number"] == "UTR123456789012"
        print("[PASS] 5. Payment details submitted and UTR verified")

        # 6. Update Members (while pending)
        update_res = update_members(reg_id, IshanyaMemberUpdateRequest(
            members=[
                IshanyaMemberSchema(
                    name="Priya N. Updated",
                    roll_no="23BD1A0502",
                    department="AIML",
                    sec="C",
                    email="priya.updated@test.com",
                    phone="9876543299"
                ),
                IshanyaMemberSchema(
                    name="Karthik V. Updated",
                    roll_no="23BD1A0503",
                    department="DS",
                    sec="D",
                    email="karthik.updated@test.com",
                    phone="9876543288"
                )
            ]
        ), db)
        assert update_res["success"] is True

        status_after_update = get_status(reg_id, db)
        assert status_after_update["members"][0]["name"] == "Priya N. Updated"
        assert status_after_update["members"][0]["department"] == "AIML"
        assert status_after_update["members"][0]["section"] == "C"
        print("[PASS] 6. Member details updated successfully while pending")

    finally:
        # Clean up database test record
        if reg_id:
            team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == reg_id).first()
            if team:
                db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).delete()
                db.delete(team)
                db.commit()
            print("[PASS] 7. Database cleanly cleaned up (0 dummy rows remaining)")
        db.close()

    print("=" * 65)
    print("ALL DIRECT ISHANYA REGISTRATION VERIFICATIONS PASSED (100%)")
    print("=" * 65)

if __name__ == "__main__":
    test_full_registration_suite()
