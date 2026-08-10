from flask import Blueprint, request, jsonify
from models.registration import REGISTRATION
from utills.sheets import SHEETSMANAGER
from config.settings import CONFIG


userregistration_bp = Blueprint('userregistration', __name__)
sheets_manager = SHEETSMANAGER()

@userregistration_bp.route('/userregistration/', methods=['POST', 'OPTIONS'])
@userregistration_bp.route('/applications', methods=['POST', 'OPTIONS'])
def RegisterUser():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    if not data:
        return jsonify({"report": "No data provided", "error": {"message": "No data provided"}}), 400

    # Extract fields flexibly (supporting both camelCase from frontend and lowercase)
    fullname = (data.get('fullname') or data.get('fullName') or '').strip()
    emailaddress = (data.get('emailaddress') or data.get('collegeEmail') or '').strip()
    rollnumber = (data.get('rollnumber') or data.get('rollNumber') or '').strip()
    mobilenumber = (data.get('mobilenumber') or data.get('phone') or '').strip()
    department = (data.get('department') or data.get('academicDepartment') or '').strip()
    section = (data.get('section') or '').strip()
    year = str(data.get('year') or '').strip()
    
    primary_pref = data.get('portfolio') or data.get('primaryPortfolio') or ''
    secondary_pref = data.get('secondaryPortfolio') or ''
    portfolio = f"{primary_pref} / {secondary_pref}".strip(' /') if secondary_pref else primary_pref
    
    knowaboutaarna = (data.get('knowaboutaarna') or data.get('experience') or 'N/A').strip()
    whyjoinaarna = (data.get('whyjoinaarna') or data.get('motivation') or 'N/A').strip()
    skills = (data.get('skills') or 'N/A').strip()
    
    try:
        leadership_rating = int(data.get('leadershiprating') or 5)
    except (ValueError, TypeError):
        leadership_rating = 5

    previous_club = data.get('previousclub', '')
    current_club = data.get('currentclub', '')

    if not fullname or not emailaddress or not rollnumber:
        return jsonify({
            "report": "Missing required fields",
            "error": {"message": "Full name, email, and roll number are required"}
        }), 400

    # Save to Database
    try:
        new_registration = REGISTRATION(
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
            leadershiprating=leadership_rating
        )
        new_registration.SaveRegistration()
    except Exception as e:
        print(f"Database error during registration: {str(e)}")
        return jsonify({
            "report": f"Database error: {str(e)}",
            "error": {"message": f"Database error: {str(e)}"}
        }), 500

    # Save to Google Sheets (safely)
    try:
        row_data = [
            fullname, emailaddress, rollnumber, mobilenumber,
            department, section, year, portfolio,
            knowaboutaarna, whyjoinaarna, skills,
            previous_club, current_club, leadership_rating
        ]
        sheets_manager.AppendRow(row_data)
    except Exception as sheets_err:
        print(f"Warning: Failed to upload to Google Sheets: {sheets_err}")

    # Success Response
    return jsonify({
        "success": True,
        "report": "Registration successful! Please join our WhatsApp group.",
        "message": "Application submitted successfully!",
        "whatsapplink": CONFIG.WHATSAPP_GROUP_LINK
    }), 200

