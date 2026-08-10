from flask import Blueprint, request, jsonify
from backend.models.registration import db, ADMIN, REGISTRATION
from backend.utills.auth import GenerateToken, token_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['POST'])
def Login():
    data = request.get_json()
    if not data or 'rollnumber' not in data or 'password' not in data:
        return jsonify({'report': 'Roll number and password are required'}), 400

    admin = ADMIN.query.filter_by(rollnumber=data['rollnumber'].strip().upper()).first()
    if not admin or not admin.CheckPassword(data['password']):
        return jsonify({'report': 'Invalid credentials'}), 401

    token = GenerateToken(admin.id)
    return jsonify({
        'token': token,
        'admin': {
            'id': admin.id,
            'rollnumber': admin.rollnumber,
            'role': admin.role,
            'assigned_department': admin.assigned_department,
            'assigned_section': admin.assigned_section
        }
    }), 200

@admin_bp.route('/me', methods=['GET'])
@token_required
def GetMe(current_admin):
    return jsonify({
        'admin': {
            'id': current_admin.id,
            'rollnumber': current_admin.rollnumber,
            'role': current_admin.role,
            'assigned_department': current_admin.assigned_department,
            'assigned_section': current_admin.assigned_section
        }
    }), 200

@admin_bp.route('/create', methods=['POST'])
@token_required
def CreateSubAdmin(current_admin):
    if current_admin.role != 'superadmin':
        return jsonify({'report': 'Only Super Admins can create sub-admins'}), 403

    data = request.get_json()
    if not data or 'rollnumber' not in data or 'password' not in data:
        return jsonify({'report': 'Roll number and password are required'}), 400

    rollnumber = data['rollnumber'].strip().upper()
    existing = ADMIN.query.filter_by(rollnumber=rollnumber).first()
    if existing:
        return jsonify({'report': 'An admin with this roll number already exists'}), 400

    assigned_department = data.get('assigned_department', '').strip()
    assigned_section = data.get('assigned_section', '').strip()

    new_admin = ADMIN(
        rollnumber=rollnumber,
        role='subadmin',
        assigned_department=assigned_department if assigned_department else None,
        assigned_section=assigned_section if assigned_section else None
    )
    new_admin.SetPassword(data['password'])
    new_admin.SaveAdmin()

    return jsonify({'report': 'Sub-Admin created successfully!'}), 201

@admin_bp.route('/subadmins', methods=['GET'])
@token_required
def ListSubAdmins(current_admin):
    if current_admin.role != 'superadmin':
        return jsonify({'report': 'Only Super Admins can view sub-admins list'}), 403

    subadmins = ADMIN.query.filter_by(role='subadmin').all()
    result = []
    for sa in subadmins:
        result.append({
            'id': sa.id,
            'rollnumber': sa.rollnumber,
            'assigned_department': sa.assigned_department or 'All',
            'assigned_section': sa.assigned_section or 'All'
        })
    return jsonify({'subadmins': result}), 200

@admin_bp.route('/applicants', methods=['GET'])
@token_required
def GetApplicants(current_admin):
    query = REGISTRATION.query

    if current_admin.role == 'subadmin':
        if current_admin.assigned_department:
            query = query.filter(REGISTRATION.department.ilike(current_admin.assigned_department))
        if current_admin.assigned_section:
            query = query.filter(REGISTRATION.section.ilike(current_admin.assigned_section))

    applicants = query.all()
    result = []
    for app in applicants:
        result.append({
            'id': app.id,
            'fullname': app.fullname,
            'emailaddress': app.emailaddress,
            'rollnumber': app.rollnumber,
            'mobilenumber': app.mobilenumber,
            'department': app.department,
            'section': app.section,
            'year': app.year,
            'portfolio': app.portfolio,
            'knowaboutaarna': app.knowaboutaarna,
            'whyjoinaarna': app.whyjoinaarna,
            'skills': app.skills,
            'previousclub': app.previousclub or 'N/A',
            'currentclub': app.currentclub or 'N/A',
            'leadershiprating': app.leadershiprating
        })

    return jsonify({'applicants': result}), 200
