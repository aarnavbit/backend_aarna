import sys
import re
import requests
from app.database import SessionLocal
from app.models.ishanya import IshanyaTeam, IshanyaMember
from app.config import settings

BASE_URL = "http://localhost:8000"

def run_tests():
    print("=" * 60)
    print("STARTING ISHANYA REGISTRATION SYSTEM E2E TEST SUITE")
    print("=" * 60)
    passed_tests = 0
    total_tests = 0

    def record_pass(test_name):
        nonlocal passed_tests, total_tests
        total_tests += 1
        passed_tests += 1
        print(f"  [PASS] {test_name}")

    def record_fail(test_name, reason):
        nonlocal total_tests
        total_tests += 1
        print(f"  [FAIL] {test_name}: {reason}")
        raise AssertionError(f"{test_name} failed: {reason}")

    reg_id = None

    try:
        # ---------------------------------------------------------
        # Checkpoint 1: Registration Validation (Invalid Member Count)
        # ---------------------------------------------------------
        print("\n--- Checkpoint 1: Registration Validation ---")
        invalid_payload = {
            "team_name": "Test Team Alpha",
            "leader_name": "Alice Leader",
            "leader_email": "alice@example.com",
            "leader_phone": "9876543210",
            "members": [
                {"name": "Bob Member", "phone": "9876543211"}
            ]  # Only 1 member instead of 2
        }
        res = requests.post(f"{BASE_URL}/api/ishanya/register", json=invalid_payload)
        if res.status_code == 400 and "additional member" in res.json().get("detail", ""):
            record_pass("Registration rejects invalid member count (HTTP 400)")
        else:
            record_fail("Registration rejects invalid member count", f"Got status {res.status_code}: {res.text}")

        # ---------------------------------------------------------
        # Checkpoint 2: Successful Registration (Leader + 2 members)
        # ---------------------------------------------------------
        print("\n--- Checkpoint 2: Team Registration (Leader + 2 Members) ---")
        reg_payload = {
            "team_name": "Tech Titans",
            "leader_name": "Rohit Sharma",
            "leader_email": "rohit.titans@example.com",
            "leader_phone": "+919876543210",
            "members": [
                {"name": "Virat Kohli", "phone": "+919876543211"},
                {"name": "Jasprit Bumrah", "phone": "+919876543212"}
            ]
        }
        res = requests.post(f"{BASE_URL}/api/ishanya/register", json=reg_payload)
        data = res.json()
        if res.status_code == 200 and data.get("success") is True and "registration_id" in data:
            reg_id = data["registration_id"]
            if re.match(r"^ISH-[A-Z0-9]{4}$", reg_id):
                record_pass(f"Team registered successfully with valid registration ID format ({reg_id})")
            else:
                record_fail("Registration ID format", f"ID '{reg_id}' does not match ISH-XXXX pattern")
        else:
            record_fail("Team registration", f"Status {res.status_code}: {res.text}")

        # ---------------------------------------------------------
        # Checkpoint 3: Status Retrieval (Pending State)
        # ---------------------------------------------------------
        print("\n--- Checkpoint 3: Status Retrieval (Pending) ---")
        res = requests.get(f"{BASE_URL}/api/ishanya/status/{reg_id}")
        data = res.json()
        if (
            res.status_code == 200
            and data.get("registration_id") == reg_id
            and data.get("team_name") == "Tech Titans"
            and data.get("leader_name") == "Rohit Sharma"
            and data.get("status") == "pending"
            and len(data.get("members", [])) == 2
            and "whatsapp_link" not in data  # WhatsApp link must NOT show when pending
        ):
            record_pass("Public status returns pending state, leader details, 2 members, no WhatsApp link")
        else:
            record_fail("Status retrieval (pending)", f"Response: {data}")

        # ---------------------------------------------------------
        # Checkpoint 4: Payment Submission (UTR + Base64 screenshot)
        # ---------------------------------------------------------
        print("\n--- Checkpoint 4: Payment Submission ---")
        dummy_screenshot = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        payment_payload = {
            "registration_id": reg_id,
            "utr_number": "UTR12345678999",
            "screenshot_base64": dummy_screenshot
        }
        res = requests.post(f"{BASE_URL}/api/ishanya/payment", json=payment_payload)
        data = res.json()
        if res.status_code == 200 and data.get("success") is True:
            record_pass("Payment submitted successfully (HTTP 200)")
        else:
            record_fail("Payment submission", f"Status {res.status_code}: {res.text}")

        # Verify payment reflected in status
        res = requests.get(f"{BASE_URL}/api/ishanya/status/{reg_id}")
        if res.json().get("utr_number") == "UTR12345678999":
            record_pass("Status query reflects submitted UTR number")
        else:
            record_fail("UTR verification in status", f"Status response: {res.text}")

        # ---------------------------------------------------------
        # Checkpoint 5: Member Update (While Pending)
        # ---------------------------------------------------------
        print("\n--- Checkpoint 5: Member Update (While Pending) ---")
        update_payload = {
            "members": [
                {"name": "Suryakumar Yadav", "phone": "+919876543222"},
                {"name": "Hardik Pandya", "phone": "+919876543223"}
            ]
        }
        res = requests.put(f"{BASE_URL}/api/ishanya/members/{reg_id}", json=update_payload)
        data = res.json()
        if res.status_code == 200 and data.get("success") is True:
            record_pass("Member details updated successfully while pending")
        else:
            record_fail("Member update", f"Status {res.status_code}: {res.text}")

        # Verify members updated in status
        res = requests.get(f"{BASE_URL}/api/ishanya/status/{reg_id}")
        members = res.json().get("members", [])
        member_names = [m["name"] for m in members]
        if "Suryakumar Yadav" in member_names and "Hardik Pandya" in member_names:
            record_pass("Status query reflects updated member names")
        else:
            record_fail("Updated members in status", f"Members found: {members}")

        # ---------------------------------------------------------
        # Checkpoint 6: Admin Authentication & Admin Endpoints
        # ---------------------------------------------------------
        print("\n--- Checkpoint 6: Admin Auth & Management Endpoints ---")
        login_res = requests.post(f"{BASE_URL}/admin/login", json={
            "rollnumber": settings.DEFAULT_SUPERADMIN_ROLL,
            "password": settings.DEFAULT_SUPERADMIN_PASS
        })
        if login_res.status_code != 200 or "token" not in login_res.json():
            record_fail("Admin login", f"Status {login_res.status_code}: {login_res.text}")
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        record_pass("Admin logged in and retrieved JWT token")

        # Admin: List teams
        res = requests.get(f"{BASE_URL}/api/ishanya/admin/teams", headers=headers)
        if res.status_code == 200 and res.json().get("count", 0) >= 1:
            teams = res.json()["teams"]
            matching = [t for t in teams if t["registration_id"] == reg_id]
            if matching:
                record_pass(f"Admin team listing includes registered team ({reg_id})")
            else:
                record_fail("Admin team listing", f"Team {reg_id} not found in listing")
        else:
            record_fail("Admin list teams", f"Status {res.status_code}: {res.text}")

        # Admin: View payment screenshot
        res = requests.get(f"{BASE_URL}/api/ishanya/admin/teams/{reg_id}/screenshot", headers=headers)
        if res.status_code == 200 and res.json().get("screenshot") == dummy_screenshot:
            record_pass("Admin screenshot retrieval verified")
        else:
            record_fail("Admin get screenshot", f"Status {res.status_code}: {res.text}")

        # ---------------------------------------------------------
        # Checkpoint 7: Admin Status Update to 'accepted' & Email Trigger
        # ---------------------------------------------------------
        print("\n--- Checkpoint 7: Admin Status Transition & Email Trigger ---")
        res = requests.put(
            f"{BASE_URL}/api/ishanya/admin/teams/{reg_id}/status",
            headers=headers,
            json={"status": "accepted", "notes": "Approved by Committee"}
        )
        data = res.json()
        if res.status_code == 200 and data.get("success") is True:
            record_pass("Admin updated status to 'accepted'")
        else:
            record_fail("Admin update status", f"Status {res.status_code}: {res.text}")

        # Public status query must now show 'accepted' AND the WhatsApp group link
        res = requests.get(f"{BASE_URL}/api/ishanya/status/{reg_id}")
        data = res.json()
        if (
            res.status_code == 200
            and data.get("status") == "accepted"
            and data.get("admin_notes") == "Approved by Committee"
            and data.get("whatsapp_link") == settings.ISHANYA_WHATSAPP_GROUP_LINK
        ):
            record_pass("Accepted status includes admin notes and WhatsApp group link")
        else:
            record_fail("Accepted status check", f"Data: {data}")

        # ---------------------------------------------------------
        # Checkpoint 8: Member Update Blocked When Accepted
        # ---------------------------------------------------------
        print("\n--- Checkpoint 8: Member Update Guardrail ---")
        res = requests.put(f"{BASE_URL}/api/ishanya/members/{reg_id}", json=update_payload)
        if res.status_code == 400 and "pending" in res.json().get("detail", ""):
            record_pass("Member update rejected when status is not 'pending' (HTTP 400)")
        else:
            record_fail("Member update guardrail", f"Expected 400, got {res.status_code}: {res.text}")

    finally:
        # ---------------------------------------------------------
        # Checkpoint 9: Database Cleanup
        # ---------------------------------------------------------
        print("\n--- Checkpoint 9: Database Cleanup ---")
        if reg_id:
            db = SessionLocal()
            try:
                team = db.query(IshanyaTeam).filter(IshanyaTeam.registration_id == reg_id).first()
                if team:
                    db.query(IshanyaMember).filter(IshanyaMember.team_id == team.id).delete()
                    db.delete(team)
                    db.commit()
                # Verify counts
                remaining_teams = db.query(IshanyaTeam).count()
                remaining_members = db.query(IshanyaMember).count()
                if remaining_teams == 0 and remaining_members == 0:
                    record_pass("All dummy test records cleanly deleted from database (0 remaining)")
                else:
                    print(f"  [WARN] Remaining teams: {remaining_teams}, members: {remaining_members}")
            except Exception as e:
                db.rollback()
                print(f"  [ERROR] Cleanup failed: {e}")
            finally:
                db.close()

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed_tests} / {total_tests} CHECKS PASSED (100%)")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
