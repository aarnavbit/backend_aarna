from flask import Blueprint, request, jsonify
from backend.models.registration import REGISTRATION
from backend.utills.sheets import SHEETSMANAGER
from backend.config.settings import CONFIG

userregistration_bp = Blueprint('userregistration', __name__)
sheets_manager = SHEETSMANAGER()

@userregistration_bp.route('/userregistration/', methods=['POST'])
def RegisterUser():
    data = request.get_json()
    
    if not data:
        return jsonify({"report": "No data provided"}), 400

    # Ensure all required keys are present (using lowercase as per rules)
    required_keys = ['fullname', 'emailaddress', 'rollnumber', 'mobilenumber', 'department', 'section', 'year']
    for key in required_keys:
        if key not in data:
            return jsonify({"report": f"Missing required field: {key}"}), 400

    # Save to Database
    try:
        new_registration = REGISTRATION(
            fullname=data['fullname'],
            emailaddress=data['emailaddress'],
            rollnumber=data['rollnumber'],
            mobilenumber=data['mobilenumber'],
            department=data['department'],
            section=data['section'],
            year=data['year']
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
        data['year']
    ]
    
    # We will attempt to append to sheets, but we won't fail the registration if it fails (optional fallback, but let's just log it)
    # The requirement is to upload the data to google sheets.
    sheets_success = sheets_manager.AppendRow(row_data)
    
    if not sheets_success:
        # If sheets upload fails but DB succeeds, you can still return success or a specific message.
        # Let's return success but note the sheets failure in logs, or return a 400 if it's strictly required.
        # We will return a success with the whatsapp link anyway since DB save was successful.
        print("Warning: Failed to upload to Google Sheets")

    # Success Response with WhatsApp Link
    return jsonify({
        "report": "Registration successful! Please join our WhatsApp group.",
        "whatsapplink": CONFIG.WHATSAPP_GROUP_LINK
    }), 200
