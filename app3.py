import streamlit as st
from streamlit_autorefresh import st_autorefresh
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')

# 🔁 Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="refresh")

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_path = r"C:\Users\USER\Videos\cow-management-app-461516-fdac9aa4f0a2.json"
creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)
sheet = client.open('Cow Management Input').sheet1

# Read data
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Dashboard
st.title("🐄 Real-Time Cow Management Dashboard")
st.write(f"Total Records: {len(df)}")

if 'Breed' in df.columns:
    st.subheader("Breed Distribution")
    breed_counts = df['Breed'].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(breed_counts, labels=breed_counts.index, autopct='%1.1f%%')
    ax1.axis('equal')
    st.pyplot(fig1)

if 'Age' in df.columns:
    st.subheader("Age Distribution")
    fig2, ax2 = plt.subplots()
    sns.histplot(df['Age'], bins=10, kde=True, ax=ax2, color='skyblue')
    st.pyplot(fig2)

st.header("Data Preview")
st.dataframe(df.head())
