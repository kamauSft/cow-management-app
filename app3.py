import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta

sns.set_style('whitegrid')

# --- Custom CSS ---
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
    footer { visibility: hidden; }
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
    unsafe_allow_html=True,
)

# --- Google Sheets API Setup ---
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_path = r"C:\Users\USER\Videos\cow-management-app-461516-fdac9aa4f0a2.json"  # Update your path here
creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)
sheet = client.open('Cow Management Input').sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Fix date columns
if 'Date of Birth' in df.columns:
    df['Date of Birth'] = pd.to_datetime(df['Date of Birth'], errors='coerce')

if 'Insemination Date' in df.columns:
    df['Expected Birth Date'] = pd.to_datetime(df['Insemination Date'], errors='coerce') + timedelta(days=283)

st.title("🐄 Robust Cow Management Dashboard")
st.markdown("""
Welcome to the Cow Management Dashboard!  
Track your herd's health, expenses, income, and profitability in real time.  
Make informed decisions based on accurate, up-to-date data.
""")

# Total count of cows
total_cows = df['Cow ID'].nunique() if 'Cow ID' in df.columns else 0
st.markdown(f"### Total Number of Cows: **{total_cows}**")

# Sidebar inputs
st.sidebar.header("Settings")
milk_price_morning = st.sidebar.number_input("Milk Price Morning per Liter", 0.0, 1000.0, 40.0, 0.5)
milk_price_mid_morning = st.sidebar.number_input("Milk Price Mid Morning per Liter", 0.0, 1000.0, 38.0, 0.5)
milk_price_evening = st.sidebar.number_input("Milk Price Evening per Liter", 0.0, 1000.0, 42.0, 0.5)

reorder_threshold_default = 50  # Default threshold for feed reorder

# Expense columns (note trailing space on 'Pregnancy Test Cost ')
expense_columns = [
    'Expenses: Feed', 'Expenses: Labor', 'Expenses: Utilities',
    'Salt Cost', 'Silage Cost', 'Vaccination Cost', 'Milking Labor Cost',
    'Electricity Cost', 'Other Medical Costs', 'AI Cost', 'Pregnancy Test Cost '
]

# Milk columns (exact names including spaces)
milk_morning_col = 'Milk Morning (L)'
milk_mid_morning_col = 'Milk Mid Morning  (L)'  # double spaces after 'Morning'
milk_evening_col = 'Sold Milk Evening  (L)'    # double spaces after 'Evening'

milk_columns_available = [c for c in [milk_morning_col, milk_mid_morning_col, milk_evening_col] if c in df.columns]

# Convert milk columns to numeric (fixes multiplication errors)
for col in milk_columns_available:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Convert expense columns to numeric to avoid subtraction errors
for col in expense_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

if all(x in df.columns for x in ['Cow ID'] + expense_columns) and len(milk_columns_available) > 0:
    df['Income Morning'] = df[milk_morning_col] * milk_price_morning if milk_morning_col in df.columns else 0
    df['Income Mid Morning'] = df[milk_mid_morning_col] * milk_price_mid_morning if milk_mid_morning_col in df.columns else 0
    df['Income Evening'] = df[milk_evening_col] * milk_price_evening if milk_evening_col in df.columns else 0
    df['Income'] = df[['Income Morning', 'Income Mid Morning', 'Income Evening']].sum(axis=1)
    df['Total Expenses'] = df[expense_columns].sum(axis=1)
    df['Profit'] = df['Income'] - df['Total Expenses']
else:
    st.warning("Milk or expense columns missing, profitability won't be calculated.")

# Break-even analysis and farm profit/loss alert
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
            st.success("✅ Farm is currently PROFITABLE.")
        else:
            st.error("⚠️ Farm is currently RUNNING AT A LOSS.")
    
    fig, ax = plt.subplots()
    ax.bar(['Income', 'Expenses'], [total_income, total_expenses], color=['#4CAF50', '#F44336'])
    ax.set_ylabel("Ksh")
    ax.set_title("Total Income vs Expenses")
    st.pyplot(fig)
else:
    st.info("Profitability data unavailable.")

# Feed reorder alerts
st.header("⚠️ Feed Reorder Alerts")

feed_stock_col = 'Feeds (kg)'

if feed_stock_col in df.columns:
    df[feed_stock_col] = pd.to_numeric(df[feed_stock_col], errors='coerce')
    low_feed = df[df[feed_stock_col] <= reorder_threshold_default]
    if not low_feed.empty:
        st.warning(f"Feeds that need reordering (threshold ≤ {reorder_threshold_default} kg):")
        for idx, row in low_feed.iterrows():
            st.write(f"- Cow ID: {row.get('Cow ID', 'N/A')}, Feeds (kg): {row[feed_stock_col]}")
        st.info("Please consider ordering feeds to avoid stockouts.")
    else:
        st.success("All feed stocks are above reorder threshold.")
else:
    st.info(f"Feed stock column '{feed_stock_col}' not found.")

# Most profitable and most expensive cows
st.header("🐮 Cow Profitability Ranking")
if 'Profit' in df.columns and 'Cow ID' in df.columns:
    top_profit = df[['Cow ID', 'Profit']].sort_values('Profit', ascending=False).head(5)
    top_expense = df[['Cow ID', 'Total Expenses']].sort_values('Total Expenses', ascending=False).head(5)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 5 Most Profitable Cows")
        st.table(top_profit.set_index('Cow ID'))
    with col2:
        st.subheader("Top 5 Most Expensive Cows")
        st.table(top_expense.set_index('Cow ID'))
else:
    st.info("Profitability data unavailable for cows.")

# Farm valuation
st.header("💰 Farm Valuation")
valuation_col = 'valuation '
if valuation_col in df.columns:
    df[valuation_col] = pd.to_numeric(df[valuation_col].astype(str).str.replace(',', ''), errors='coerce')
    total_valuation = df[valuation_col].sum()
    st.write(f"Total Farm Valuation from Cow Assets: **Ksh {total_valuation:,.2f}**")
else:
    st.info("Valuation column missing or misnamed (check trailing spaces).")

# Filters
st.header("🔍 Filter & Explore Data")
filtered_df = df.copy()

if 'Date of Birth' in df.columns:
    min_date = df['Date of Birth'].min()
    max_date = df['Date of Birth'].max()
    date_range = st.date_input("Select Date of Birth Range", [min_date, max_date])
    filtered_df = filtered_df[
        (filtered_df['Date of Birth'] >= pd.to_datetime(date_range[0])) &
        (filtered_df['Date of Birth'] <= pd.to_datetime(date_range[1]))
    ]

search_term = st.text_input("Search Cow by ID or Name")
if search_term:
    filtered_df = filtered_df[
        filtered_df['Cow ID'].astype(str).str.contains(search_term, case=False, na=False) |
        filtered_df.get('Name', pd.Series(dtype=str)).astype(str).str.contains(search_term, case=False, na=False)
    ]

# Cumulative Number of Cows Over Time
st.header("📊 Cumulative Number of Cows Over Time")
if 'Date of Birth' in filtered_df.columns:
    birth_counts = filtered_df.groupby('Date of Birth')['Cow ID'].nunique().sort_index()
    count_df = birth_counts.cumsum().reset_index()
    count_df.rename(columns={'Cow ID': 'Cumulative Number of Cows'}, inplace=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.lineplot(data=count_df, x='Date of Birth', y='Cumulative Number of Cows', marker='o', ax=ax)
    ax.set_xlabel("Date of Birth")
    ax.set_ylabel("Cumulative Number of Cows")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.info("Date of Birth column missing for cumulative cow count plot.")

# Pie chart: Cow Category distribution
if 'Cow Category' in df.columns:
    st.header("📊 Cow Category Distribution")
    category_counts = df['Cow Category'].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette('pastel'))
    ax1.axis('equal')
    st.pyplot(fig1)

# Pie chart: Profit vs Loss distribution
if 'Profit' in df.columns:
    st.header("📊 Profit vs Loss Distribution")
    profit_loss_counts = pd.Series({
        'Profit': (df['Profit'] > 0).sum(),
        'Loss': (df['Profit'] <= 0).sum()
    })
    fig2, ax2 = plt.subplots()
    ax2.pie(profit_loss_counts, labels=profit_loss_counts.index, autopct='%1.1f%%', startangle=90, colors=['#4CAF50', '#F44336'])
    ax2.axis('equal')
    st.pyplot(fig2)

# Time series plots (2 per row)
st.header("📈 Time Series Plots")
numeric_cols = [c for c in filtered_df.select_dtypes(include='number').columns if c not in ['Cow ID', 'Tag Number']]

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

# Data preview
st.header("📋 Data Preview")
st.dataframe(filtered_df)

# Footer
st.markdown("""
<div class="footer-style">
Built with Python, Google Sheets API, and Streamlit pipelines
</div>
""", unsafe_allow_html=True)
