import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta

sns.set_style('whitegrid')

# --- Custom CSS for background and style ---
st.markdown(
    """
    <style>
    .stApp, .main {
        background-color: #f0f4f8 !important;  /* Soft light blue-gray */
        color: #333333;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .css-1d391kg, .css-1v3fvcr {
        background-color: white !important;
        padding: 1rem !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgb(0 0 0 / 0.1) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Google Sheets API Setup ---
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_path = r"C:\Users\USER\Videos\cow-management-app-461516-fdac9aa4f0a2.json"  # Update this path
creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)
sheet = client.open('Cow Management Input').sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Convert date columns
date_cols = ['Date of Birth']
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# Calculate Expected Birth Date from Insemination Date if available
if 'Insemination Date' in df.columns:
    df['Expected Birth Date'] = pd.to_datetime(df['Insemination Date'], errors='coerce') + timedelta(days=283)

# ---- FARM INTRODUCTION ----
st.title("🐄 Robust Cow Management Dashboard")
st.markdown("""
Welcome to the Cow Management Dashboard!  
Track your herd's health, expenses, income, and profitability in real time.  
Make informed decisions based on accurate, up-to-date data.
""")

# ---- INPUTS ----
st.sidebar.header("Settings")

# Milk prices for different milking times
milk_price_am = st.sidebar.number_input("Milk Price Morning (AM) per Liter", min_value=0.0, value=40.0, step=0.5)
milk_price_mid = st.sidebar.number_input("Milk Price Mid Morning per Liter", min_value=0.0, value=38.0, step=0.5)
milk_price_pm = st.sidebar.number_input("Milk Price Evening (PM) per Liter", min_value=0.0, value=42.0, step=0.5)

# Feed reorder threshold input
reorder_threshold = st.sidebar.number_input("Feed Reorder Threshold", min_value=0, value=50, step=1)

# --- Calculations for profitability ---

expense_columns = ['Expenses: Feed', 'Expenses: Labor', 'Expenses: Utilities',
                   'Salt Cost', 'Silage Cost', 'Vaccination Cost', 'Milking Labor Cost',
                   'Electricity Cost', 'Other Medical Costs', 'AI Cost', 'Pregnancy Test Cost']

# Milk columns - assuming these exist, add Mid Morning if you have that column (or else omit)
milk_am_col = 'Milk AM (L)'
milk_mid_col = 'Milk Mid Morning (L)'  # Adjust if you have this column, else remove references
milk_pm_col = 'Milk PM (L)'

milk_columns_available = [c for c in [milk_am_col, milk_mid_col, milk_pm_col] if c in df.columns]

if all(x in df.columns for x in ['Cow ID'] + expense_columns) and len(milk_columns_available) > 0:
    # Total milk per milking time
    df['Income AM'] = df[milk_am_col] * milk_price_am if milk_am_col in df.columns else 0
    df['Income Mid'] = df[milk_mid_col] * milk_price_mid if milk_mid_col in df.columns else 0
    df['Income PM'] = df[milk_pm_col] * milk_price_pm if milk_pm_col in df.columns else 0
    # Total Income per cow
    df['Income'] = df[['Income AM', 'Income Mid', 'Income PM']].sum(axis=1)
    # Total Expenses
    df['Total Expenses'] = df[expense_columns].sum(axis=1)
    # Profit
    df['Profit'] = df['Income'] - df['Total Expenses']
else:
    st.warning("Some milk or expense columns missing, profitability and valuation won't be calculated.")

# ---- Break-even point calculation ----
st.header("📊 Break-Even Analysis")

if 'Income' in df.columns and 'Total Expenses' in df.columns:
    total_income = df['Income'].sum()
    total_expenses = df['Total Expenses'].sum()
    break_even = total_income >= total_expenses

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Income (Ksh)", f"{total_income:,.2f}")
        st.metric("Total Expenses (Ksh)", f"{total_expenses:,.2f}")
    with col2:
        if break_even:
            st.success("✅ Farm is currently profitable (Income ≥ Expenses)")
        else:
            st.error("⚠️ Farm is running at a loss (Income < Expenses)")

    # Income vs Expenses bar chart
    fig, ax = plt.subplots()
    ax.bar(['Income', 'Expenses'], [total_income, total_expenses], color=['#4CAF50', '#F44336'])
    ax.set_ylabel("Ksh")
    ax.set_title("Total Income vs Expenses")
    st.pyplot(fig)
else:
    st.info("Profitability data unavailable.")

# ---- Feed Reorder Alerts ----
st.header("⚠️ Feed Reorder Alerts")

if 'Feed Stock' in df.columns:
    low_feed = df[df['Feed Stock'] <= reorder_threshold]
    if not low_feed.empty:
        st.warning(f"Feeds to reorder (stock ≤ {reorder_threshold}):")
        st.dataframe(low_feed[['Feed Name', 'Feed Stock']])
    else:
        st.success("All feed stocks are sufficient.")
else:
    st.info("Feed Stock data unavailable.")

# ---- Most Profitable and Most Expensive Cows ----
st.header("🐮 Cow Profitability Ranking")

if 'Profit' in df.columns and 'Cow ID' in df.columns:
    top_profit = df[['Cow ID', 'Profit']].sort_values(by='Profit', ascending=False).head(5)
    top_expense = df[['Cow ID', 'Total Expenses']].sort_values(by='Total Expenses', ascending=False).head(5)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 5 Most Profitable Cows")
        st.table(top_profit.set_index('Cow ID'))
    with col2:
        st.subheader("Top 5 Most Expensive Cows")
        st.table(top_expense.set_index('Cow ID'))
else:
    st.info("Profitability data unavailable for cows.")

# ---- Farm Valuation Section ----
st.header("💰 Farm Valuation")

if 'Income' in df.columns:
    total_income = df['Income'].sum()
    st.write(f"Estimated Farm Value based on current milk prices: **Ksh {total_income:,.2f}**")
else:
    st.info("Income data unavailable for valuation.")

# --- Data Filtering by Date of Birth ---
st.header("🔍 Filter & Explore Data by Date of Birth")

if 'Date of Birth' in df.columns:
    min_date = df['Date of Birth'].min()
    max_date = df['Date of Birth'].max()
    date_range = st.date_input("Select Date of Birth Range", [min_date, max_date])
    filtered_df = df[(df['Date of Birth'] >= pd.to_datetime(date_range[0])) &
                     (df['Date of Birth'] <= pd.to_datetime(date_range[1]))]
else:
    filtered_df = df.copy()

# --- Time Series Plots (2 per row) ---
st.header("📈 Time Series Plots")

numeric_cols = [col for col in filtered_df.select_dtypes(include=['number']).columns.tolist() if col not in ['Cow ID', 'Tag Number']]

for i in range(0, len(numeric_cols), 2):
    cols = st.columns(2)
    for j, col_name in enumerate(numeric_cols[i:i+2]):
        with cols[j]:
            st.subheader(f"{col_name} Over Time")
            if 'Date of Birth' in filtered_df.columns:
                fig, ax = plt.subplots(figsize=(6, 3.5))
                sns.lineplot(data=filtered_df, x='Date of Birth', y=col_name, marker='o', ax=ax)
                ax.set_xlabel("Date of Birth")
                ax.set_ylabel(col_name)
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.write(f"Cannot plot {col_name} - 'Date of Birth' missing.")

# --- Pie Charts (2 per row) ---
st.header("📊 Categorical Data Distributions")

categorical_cols = filtered_df.select_dtypes(include=['object']).columns.tolist()

for i in range(0, len(categorical_cols), 2):
    cols = st.columns(2)
    for j, col_name in enumerate(categorical_cols[i:i+2]):
        with cols[j]:
            st.subheader(f"{col_name} Distribution")
            counts = filtered_df[col_name].value_counts()
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140)
            ax.axis('equal')
            plt.tight_layout()
            st.pyplot(fig)

# --- Data Preview ---
st.header("📋 Data Preview")
st.dataframe(filtered_df)
