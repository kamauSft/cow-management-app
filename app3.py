import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_path = r"C:\Users\USER\Videos\cow-management-app-461516-fdac9aa4f0a2.json"  # Update this if needed
creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)

# Open your spreadsheet
sheet = client.open("Cow Management Input").sheet1  # Ensure name is correct
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Print exact column names
print("\n--- Exact Column Names in the Sheet ---")
for col in df.columns:
    print(f"'{col}'")
