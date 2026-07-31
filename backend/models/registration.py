from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class REGISTRATION(db.Model):
    __tablename__ = 'registration'
    
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    emailaddress = db.Column(db.String(150), nullable=False)
    rollnumber = db.Column(db.String(50), nullable=False)
    mobilenumber = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    
    def SaveRegistration(self):
        db.session.add(self)
        db.session.commit()
