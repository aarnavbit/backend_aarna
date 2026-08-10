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
    
    # New fields
    portfolio = db.Column(db.String(100), nullable=False)
    knowaboutaarna = db.Column(db.Text, nullable=False)
    whyjoinaarna = db.Column(db.Text, nullable=False)
    skills = db.Column(db.Text, nullable=False)
    previousclub = db.Column(db.Text, nullable=True)
    currentclub = db.Column(db.Text, nullable=True)
    leadershiprating = db.Column(db.Integer, nullable=False)
    
    def SaveRegistration(self):
        db.session.add(self)
        db.session.commit()

from werkzeug.security import generate_password_hash, check_password_hash

class ADMIN(db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    rollnumber = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='subadmin') # 'superadmin' or 'subadmin'
    assigned_department = db.Column(db.String(100), nullable=True)
    assigned_section = db.Column(db.String(10), nullable=True)

    def SetPassword(self, password):
        self.password_hash = generate_password_hash(password)

    def CheckPassword(self, password):
        return check_password_hash(self.password_hash, password)

    def SaveAdmin(self):
        db.session.add(self)
        db.session.commit()

