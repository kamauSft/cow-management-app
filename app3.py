import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Define the scope for Google Sheets and Drive API access
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Use raw string for Windows path to your JSON credentials file
json_path = r"C:\Users\USER\Videos\cow-management-app-461516-fdac9aa4f0a2.json"

# Authenticate with Google API using service account credentials
creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)

# Open your Google Sheet by exact title
sheet_name = 'Cow Management Input'  # Your actual Google Sheet title
sheet = client.open(sheet_name).sheet1

# Fetch all records from the sheet
data = sheet.get_all_records()

# Load data into a pandas DataFrame
df = pd.DataFrame(data)

# Streamlit app interface
st.title("Cow Management Data Dashboard")

# Display the data table
st.dataframe(df)

# Show the total number of records
st.write(f"Total records: {len(df)}")

# Show preview of the first 5 rows
st.write("Preview of data:")
st.write(df.head())
