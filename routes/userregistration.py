from flask import Blueprint, request, jsonify
from models.registration import REGISTRATION
from utills.sheets import SHEETSMANAGER
from config.settings import CONFIG


userregistration_bp = Blueprint('userregistration', __name__)
sheets_manager = SHEETSMANAGER()

@userregistration_bp.route('/userregistration/', methods=['POST'])
def RegisterUser():
    data = request.get_json()
    
    if not data:
        return jsonify({"report": "No data provided"}), 400

    # Ensure all required keys are present
    required_keys = [
        'fullname', 'emailaddress', 'rollnumber', 'mobilenumber', 
        'department', 'section', 'year', 'portfolio', 
        'knowaboutaarna', 'whyjoinaarna', 'skills', 'leadershiprating'
    ]
    for key in required_keys:
        if key not in data:
            return jsonify({"report": f"Missing required field: {key}"}), 400

    # Handle Leadership Rating integer validation
    try:
        leadership_rating = int(data['leadershiprating'])
    except ValueError:
        return jsonify({"report": "Leadership rating must be a valid number"}), 400

    # Handle optional fields safely
    previous_club = data.get('previousclub', '')
    current_club = data.get('currentclub', '')

    # Save to Database
    try:
        new_registration = REGISTRATION(
            fullname=data['fullname'],
            emailaddress=data['emailaddress'],
            rollnumber=data['rollnumber'],
            mobilenumber=data['mobilenumber'],
            department=data['department'],
            section=data['section'],
            year=data['year'],
            portfolio=data['portfolio'],
            knowaboutaarna=data['knowaboutaarna'],
            whyjoinaarna=data['whyjoinaarna'],
            skills=data['skills'],
            previousclub=previous_club,
            currentclub=current_club,
            leadershiprating=leadership_rating
        )
        new_registration.SaveRegistration()
    except Exception as e:
        return jsonify({"report": f"Database error: {str(e)}"}), 400

    # Save to Google Sheets
    row_data = [
        data['fullname'],
        data['emailaddress'],
        data['rollnumber'],
        data['mobilenumber'],
        data['department'],
        data['section'],
        data['year'],
        data['portfolio'],
        data['knowaboutaarna'],
        data['whyjoinaarna'],
        data['skills'],
        previous_club,
        current_club,
        leadership_rating
    ]
    
    sheets_success = sheets_manager.AppendRow(row_data)
    
    if not sheets_success:
        print("Warning: Failed to upload to Google Sheets")

    # Success Response with WhatsApp Link
    return jsonify({
        "report": "Registration successful! Please join our WhatsApp group.",
        "whatsapplink": CONFIG.WHATSAPP_GROUP_LINK
    }), 200
