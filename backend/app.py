from flask import Flask
from backend.config.settings import CONFIG
from backend.models.registration import db, ADMIN
from backend.routes.userregistration import userregistration_bp
from backend.routes.admin_routes import admin_bp

def SeedSuperAdmin():
    superadmin = ADMIN.query.filter_by(role='superadmin').first()
    if not superadmin:
        default_super = ADMIN(
            rollnumber='ADMIN001',
            role='superadmin'
        )
        default_super.SetPassword('adminpassword123')
        db.session.add(default_super)
        db.session.commit()
        print("Default Super Admin seeded: Roll Number = ADMIN001, Password = adminpassword123")

def CreateApp():
    app = Flask(__name__)
    app.config.from_object(CONFIG)
    
    # Initialize Database
    db.init_app(app)
    
    # CORS setup
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,PUT,DELETE'
        return response
    
    with app.app_context():
        db.create_all()
        SeedSuperAdmin()
    
    # Register Blueprints
    app.register_blueprint(userregistration_bp)
    app.register_blueprint(admin_bp)
    
    return app

if __name__ == '__main__':
    app = CreateApp()
    app.run(debug=True)
