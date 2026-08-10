from functools import wraps
from flask import request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from backend.models.registration import ADMIN

def GetSerializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def GenerateToken(admin_id):
    serializer = GetSerializer()
    return serializer.dumps({'admin_id': admin_id})

def VerifyToken(token, max_age=86400): # Token valid for 24 hours
    serializer = GetSerializer()
    try:
        data = serializer.loads(token, max_age=max_age)
        return data.get('admin_id')
    except (SignatureExpired, BadTimeSignature):
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'report': 'Token is missing!'}), 401

        admin_id = VerifyToken(token)
        if not admin_id:
            return jsonify({'report': 'Token is invalid or expired!'}), 401

        current_admin = ADMIN.query.get(admin_id)
        if not current_admin:
            return jsonify({'report': 'Admin user not found!'}), 401

        return f(current_admin, *args, **kwargs)
    return decorated
