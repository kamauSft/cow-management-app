import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_path = r"C:\Users\USER\Videos\cow-management-app-461516-fdac9aa4f0a2.json"
creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)

sheet = client.open('Cow Management Input').sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.write("Columns in your Google Sheet:")
st.write(df.columns.tolist())
