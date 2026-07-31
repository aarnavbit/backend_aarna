from flask import Flask
from backend.config.settings import CONFIG
from backend.models.registration import db
from backend.routes.userregistration import userregistration_bp

def CreateApp():
    app = Flask(__name__)
    app.config.from_object(CONFIG)
    
    # Initialize Database
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    # Register Blueprints
    app.register_blueprint(userregistration_bp)
    
    return app

if __name__ == '__main__':
    app = CreateApp()
    app.run(debug=True)
