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
        background-color: #f0f4f8 !important;
        color: #333333;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .css-1d391kg, .css-1v3fvcr {
        background-color: white !important;
        padding: 1rem !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgb(0 0 0 / 0.1) !important;
    }
    footer {
        visibility: hidden;
    }
    .footer-style {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #f0f4f8;
        color: #666666;
        text-align: center;
        padding: 0.5rem;
        font-size: 0.9rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Google Sheets API Setup ---
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_path = r"C:\Users\USER\Videos\cow-management-app-461516-fdac9aa4f0a2.json"  # Update your path
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

# ---- Farm Introduction ----
st.title("🐄 Robust Cow Management Dashboard")
st.markdown("""
Welcome to the Cow Management Dashboard!  
Track your herd's health, expenses, income, and profitability in real time.  
Make informed decisions based on accurate, up-to-date data.
""")

# ---- Sidebar Inputs ----
st.sidebar.header("Settings")

milk_price_morning = st.sidebar.number_input("Milk Price Morning per Liter", min_value=0.0, value=40.0, step=0.5)
milk_price_mid_morning = st.sidebar.number_input("Milk Price Mid Morning per Liter", min_value=0.0, value=38.0, step=0.5)
milk_price_evening = st.sidebar.number_input("Milk Price Evening per Liter", min_value=0.0, value=42.0, step=0.5)

reorder_threshold_default = 50  # fallback if Reorder Level missing

# --- Calculations for profitability ---

expense_columns = ['Expenses: Feed', 'Expenses: Labor', 'Expenses: Utilities',
                   'Salt Cost', 'Silage Cost', 'Vaccination Cost', 'Milking Labor Cost',
                   'Electricity Cost', 'Other Medical Costs', 'AI Cost', 'Pregnancy Test Cost']

milk_morning_col = 'Milk Morning (L)'
milk_mid_morning_col = 'Milk Mid Morning (L)'
milk_evening_col = 'Milk Evening (L)'

milk_columns_available = [c for c in [milk_morning_col, milk_mid_morning_col, milk_evening_col] if c in df.columns]

if all(x in df.columns for x in ['Cow ID'] + expense_columns) and len(milk_columns_available) > 0:
    df['Income Morning'] = df[milk_morning_col] * milk_price_morning if milk_morning_col in df.columns else 0
    df['Income Mid Morning'] = df[milk_mid_morning_col] * milk_price_mid_morning if milk_mid_morning_col in df.columns else 0
    df['Income Evening'] = df[milk_evening_col] * milk_price_evening if milk_evening_col in df.columns else 0
    df['Income'] = df[['Income Morning', 'Income Mid Morning', 'Income Evening']].sum(axis=1)
    df['Total Expenses'] = df[expense_columns].sum(axis=1)
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

    fig, ax = plt.subplots()
    ax.bar(['Income', 'Expenses'], [total_income, total_expenses], color=['#4CAF50', '#F44336'])
    ax.set_ylabel("Ksh")
    ax.set_title("Total Income vs Expenses")
    st.pyplot(fig)
else:
    st.info("Profitability data unavailable.")

# ---- Feed Reorder Alerts ----
st.header("⚠️ Feed Reorder Alerts")

required_feed_cols = ['Feed Name', 'Feed Stock', 'Reorder Level']

if all(col in df.columns for col in required_feed_cols):
    feeds_to_reorder = df[df['Feed Stock'] <= df['Reorder Level']]
    if not feeds_to_reorder.empty:
        st.warning("Feeds that need reordering:")
        for _, row in feeds_to_reorder.iterrows():
            st.write(f"- **{row['Feed Name']}**: Stock = {row['Feed Stock']}, Reorder Level = {row['Reorder Level']}")
        st.info("Please consider ordering the above feeds to avoid stockouts.")
    else:
        st.success("All feed stocks are above their reorder levels. No immediate action needed.")
elif 'Feed Stock' in df.columns:
    df['Reorder Level'] = reorder_threshold_default
    feeds_to_reorder = df[df['Feed Stock'] <= df['Reorder Level']]
    if not feeds_to_reorder.empty:
        st.warning(f"Feeds that need reordering (using dummy reorder level {reorder_threshold_default}):")
        for _, row in feeds_to_reorder.iterrows():
            st.write(f"- **{row['Feed Name']}**: Stock = {row['Feed Stock']}")
        st.info("Please consider ordering the above feeds to avoid stockouts.")
    else:
        st.success("All feed stocks are above the dummy reorder level. No immediate action needed.")
else:
    st.info(f"Feed reorder alert requires columns: {', '.join(required_feed_cols)}")

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

# --- Filters by Date of Birth and Cow ID/Name ---
st.header("🔍 Filter & Explore Data")

filtered_df = df.copy()

# Filter by Date of Birth
if 'Date of Birth' in df.columns:
    min_date = df['Date of Birth'].min()
    max_date = df['Date of Birth'].max()
    date_range = st.date_input("Select Date of Birth Range", [min_date, max_date])
    filtered_df = filtered_df[(filtered_df['Date of Birth'] >= pd.to_datetime(date_range[0])) &
                              (filtered_df['Date of Birth'] <= pd.to_datetime(date_range[1]))]

# Filter by Cow ID or Name
search_term = st.text_input("Search Cow by ID or Name")
if search_term:
    filtered_df = filtered_df[
        filtered_df['Cow ID'].astype(str).str.contains(search_term, case=False, na=False) |
        filtered_df.get('Cow Name', pd.Series(dtype=str)).astype(str).str.contains(search_term, case=False, na=False)
    ]

# --- Number of Cows Over Time ---
st.header("📊 Number of Cows Over Time")

if 'Date of Birth' in filtered_df.columns:
    count_df = filtered_df.groupby('Date of Birth')['Cow ID'].nunique().reset_index()
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.lineplot(data=count_df, x='Date of Birth', y='Cow ID', marker='o', ax=ax)
    ax.set_xlabel("Date of Birth")
    ax.set_ylabel("Number of Cows")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.info("Date of Birth column missing for cow count plot.")

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

# --- Data Preview ---
st.header("📋 Data Preview")
st.dataframe(filtered_df)

# --- Footer Notification ---
st.markdown("""
<div class="footer-style">
Built with Python, Google Sheets API, and Streamlit pipelines
</div>
""", unsafe_allow_html=True)
