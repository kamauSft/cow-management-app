import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set seaborn style for nicer visuals
sns.set_style('whitegrid')

# Google Sheets API setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_path = r"C:\Users\USER\Videos\cow-management-app-461516-fdac9aa4f0a2.json"  # Update path if needed

creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)

sheet_name = 'Cow Management Input'  # Your Google Sheet title here
sheet = client.open(sheet_name).sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("🐄 Cow Management Dashboard")

# Summary
st.header("Summary Statistics")
st.write(f"Total records: {len(df)}")

# Pie chart of Breed distribution (change 'Breed' to your column name)
if 'Breed' in df.columns:
    st.subheader("Breed Distribution")
    breed_counts = df['Breed'].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(breed_counts, labels=breed_counts.index, autopct='%1.1f%%', startangle=140)
    ax1.axis('equal')  # Equal aspect ratio ensures pie is drawn as a circle.
    st.pyplot(fig1)

# Histogram of Age distribution (change 'Age' to your column name)
if 'Age' in df.columns:
    st.subheader("Age Distribution")
    fig2, ax2 = plt.subplots()
    sns.histplot(df['Age'], bins=10, kde=True, ax=ax2, color='skyblue')
    ax2.set_xlabel('Age')
    ax2.set_ylabel('Count')
    st.pyplot(fig2)

# Show preview of data
st.header("Data Preview")
st.dataframe(df.head())
