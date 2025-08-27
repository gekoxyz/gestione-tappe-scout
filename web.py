# hybrid_app.py

import gspread
import webview
from flask import Flask, render_template
from threading import Timer

# --- Configuration ---
SERVICE_ACCOUNT_FILE = 'credentials.json'
GOOGLE_SHEET_NAME = 'BACKUP Database Censiti 082025'
WORKSHEET_NAME = 'Censiti'

# --- Flask App (The Backend) ---
# This part is almost identical to our previous Flask app
app = Flask(__name__)

# Simple in-memory cache
# In a real app, you might add a timeout mechanism
cache = {
    'data': None
}

def get_sheet_data():
    """Connects to Google Sheets and fetches data, using a simple cache."""
    # For this simple example, we'll just cache the first request.
    # A real app would add a timestamp and refresh every few minutes.
    if cache['data'] is None:
        print("Fetching fresh data from Google Sheets...")
        try:
            gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
            spreadsheet = gc.open(GOOGLE_SHEET_NAME)
            worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
            data = worksheet.get_all_records()
            cache['data'] = data
            return data
        except Exception as e:
            print(f"Error fetching sheet data: {e}")
            return {'error': str(e)}
    else:
        print("Serving data from cache.")
        return cache['data']

@app.route('/')
def index():
    """Main page: displays the list of records."""
    sheet_data = get_sheet_data()
    
    if isinstance(sheet_data, dict) and 'error' in sheet_data:
        # You'd want an error.html template for this
        return f"<h1>Error</h1><p>{sheet_data['error']}</p>"
        
    if not sheet_data:
        headers = []
    else:
        headers = sheet_data[0].keys()
        
    return render_template('index.html', headers=headers, rows=sheet_data, sheet_name=GOOGLE_SHEET_NAME)

@app.route('/record/<int:row_id>')
def detail(row_id):
    """Details page: shows more info for a single record."""
    sheet_data = get_sheet_data() # Gets from cache
    
    # In gspread, row_id needs to be adjusted since lists are 0-indexed
    # and sheets are often thought of as 1-indexed. We'll use list index.
    if sheet_data and 0 <= row_id < len(sheet_data):
        record = sheet_data[row_id]
        return render_template('detail.html', record=record, row_id=row_id)
    else:
        return "Record not found", 404

# --- Main Execution (PyWebView Launcher) ---
if __name__ == '__main__':
    # # Create the PyWebView window that points to our Flask app
    # webview.create_window(
    #     f'Sheet Manager: {GOOGLE_SHEET_NAME}',
    #     app,
    #     width=1024,
    #     height=768
    #     ,debug=True
    # )
    # # Start the app
    # webview.start()
    app.run(debug=True)