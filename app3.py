import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

sns.set_style('whitegrid')

# --- Google Sheets API Setup ---
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_path = r"C:\Users\USER\Videos\cow-management-app-461516-fdac9aa4f0a2.json"  # Update your JSON path here
creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)
sheet = client.open('Cow Management Input').sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("🐄 Robust Cow Management Dashboard")

# --- Convert date columns to datetime ---
date_cols = ['Insemination Date']  # Update if you have other date columns
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# --- Calculate Expected Calf Birth Date (+283 days from Insemination) ---
if 'Insemination Date' in df.columns:
    df['Expected Birth Date'] = df['Insemination Date'] + pd.to_timedelta(283, unit='D')

# --- Summary and Alerts ---
st.header("Summary & Alerts")

# Total records
st.write(f"Total records: {len(df)}")

# Reorder Feed Alert
reorder_threshold = 50  # Adjust as needed
if 'Feed Stock' in df.columns:
    low_feed = df[df['Feed Stock'] <= reorder_threshold]
    st.subheader(f"Feeds to Reorder (Stock ≤ {reorder_threshold})")
    if not low_feed.empty:
        st.dataframe(low_feed[['Feed Name', 'Feed Stock']])
    else:
        st.write("All feed stocks are sufficient.")

# Upcoming Calves in next 30 days
if 'Expected Birth Date' in df.columns:
    st.subheader("Upcoming Calf Births (Next 30 Days)")
    today = pd.Timestamp.today()
    upcoming_births = df[(df['Expected Birth Date'] >= today) &
                         (df['Expected Birth Date'] <= today + pd.Timedelta(days=30))]
    if not upcoming_births.empty:
        st.dataframe(upcoming_births[['Cow ID', 'Expected Birth Date']])
    else:
        st.write("No expected births in the next 30 days.")

# --- Data Filtering ---
st.header("Filter & Explore Data")

if 'Insemination Date' in df.columns:
    min_date = df['Insemination Date'].min()
    max_date = df['Insemination Date'].max()
    date_range = st.date_input("Select Insemination Date Range", [min_date, max_date])
    filtered_df = df[(df['Insemination Date'] >= pd.to_datetime(date_range[0])) &
                     (df['Insemination Date'] <= pd.to_datetime(date_range[1]))]
else:
    filtered_df = df.copy()

# --- Time Series Plots ---
st.header("Time Series Plots for Numeric Parameters")

numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()

for col in numeric_cols:
    st.subheader(f"{col} over Time")
    if 'Insemination Date' in filtered_df.columns:
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.lineplot(data=filtered_df, x='Insemination Date', y=col, marker='o', ax=ax)
        ax.set_xlabel("Insemination Date")
        ax.set_ylabel(col)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.write(f"Cannot plot {col} - 'Insemination Date' column missing.")

# --- Pie Charts for Categorical Variables ---
st.header("Categorical Data Distributions")

categorical_cols = filtered_df.select_dtypes(include=['object']).columns.tolist()

for col in categorical_cols:
    st.subheader(f"{col} Distribution")
    counts = filtered_df[col].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140)
    ax.axis('equal')
    plt.tight_layout()
    st.pyplot(fig)

# --- Raw Data Preview ---
st.header("Data Preview")
st.dataframe(filtered_df)
