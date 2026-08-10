import os
from dotenv import load_dotenv

# Load the root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

class CONFIG:
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///backend.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WHATSAPP_GROUP_LINK = os.getenv('WHATSAPP_GROUP_LINK')
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    SECRET_KEY = os.getenv('SECRET_KEY', 'aarna_admin_secret_key_98765')

