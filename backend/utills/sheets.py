import gspread
from google.oauth2.service_account import Credentials
from backend.config.settings import CONFIG

class SHEETSMANAGER:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials_file = CONFIG.GOOGLE_SHEETS_CREDENTIALS_FILE
        self.sheet_id = CONFIG.GOOGLE_SHEET_ID
        self.client = None

    def Authenticate(self):
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.scopes
            )
            self.client = gspread.authorize(credentials)
            return True
        except Exception as e:
            print(f"Error authenticating with Google Sheets: {e}")
            return False

    def AppendRow(self, rowdata):
        if not self.client:
            if not self.Authenticate():
                return False
        
        try:
            sheet = self.client.open_by_key(self.sheet_id).sheet1
            sheet.append_row(rowdata)
            return True
        except Exception as e:
            print(f"Error appending row to Google Sheets: {e}")
            return False
