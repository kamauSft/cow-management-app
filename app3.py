import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta

# Set seaborn style
sns.set_style('whitegrid')

# --- Custom CSS for background and style ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f9f9f9;  /* Soft light gray background */
        color: #333333;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .css-1d391kg {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgb(0 0 0 / 0.1);
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
date_cols = ['Insemination Date']
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# Calculate Expected Birth Date
if 'Insemination Date' in df.columns:
    df['Expected Birth Date'] = df['Insemination Date'] + timedelta(days=283)

# ---- FARM INTRODUCTION ----
st.title("🐄 Robust Cow Management Dashboard")
st.markdown("""
Welcome to the Cow Management Dashboard!  
Track your herd's health, expenses, income, and profitability in real time.  
Make informed decisions based on accurate, up-to-date data.
""")

# ---- INPUTS ----
st.sidebar.header("Settings")
milk_price = st.sidebar.number_input("Current Milk Selling Price (per Liter)", min_value=0.0, value=40.0, step=0.5)

# --- Calculations for profitability ---

# Compute Total Income and Expenses per cow if available
if all(x in df.columns for x in ['Cow ID', 'Milk AM (L)', 'Milk PM (L)', 'Sold Milk (L)', 'Household Use (L)', 
                                'Expenses: Feed', 'Expenses: Labor', 'Expenses: Utilities',
                                'Salt Cost', 'Silage Cost', 'Vaccination Cost', 'Milking Labor Cost',
                                'Electricity Cost', 'Other Medical Costs', 'AI Cost', 'Pregnancy Test Cost']):
    
    # Total milk produced per cow per day (sum AM, PM, Sold, Household use)
    df['Total Milk (L)'] = df[['Milk AM (L)', 'Milk PM (L)', 'Sold Milk (L)', 'Household Use (L)']].sum(axis=1)
    # Total expenses per cow
    expense_cols = ['Expenses: Feed', 'Expenses: Labor', 'Expenses: Utilities',
                    'Salt Cost', 'Silage Cost', 'Vaccination Cost', 'Milking Labor Cost',
                    'Electricity Cost', 'Other Medical Costs', 'AI Cost', 'Pregnancy Test Cost']
    df['Total Expenses'] = df[expense_cols].sum(axis=1)
    # Income = milk price * total milk produced
    df['Income'] = df['Total Milk (L)'] * milk_price
    # Profit = Income - Expenses
    df['Profit'] = df['Income'] - df['Total Expenses']

else:
    st.warning("Some expense or milk columns missing, profitability and valuation won't be calculated.")

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
    
    # Plot Income vs Expenses bar chart
    fig, ax = plt.subplots()
    ax.bar(['Income', 'Expenses'], [total_income, total_expenses], color=['#4CAF50', '#F44336'])
    ax.set_ylabel("Ksh")
    ax.set_title("Total Income vs Expenses")
    st.pyplot(fig)
else:
    st.info("Profitability data unavailable.")

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

if 'Total Milk (L)' in df.columns:
    total_milk = df['Total Milk (L)'].sum()
    estimated_value = total_milk * milk_price
    st.write(f"Total Milk Production: {total_milk:,.2f} Liters")
    st.write(f"Estimated Farm Value based on current milk price: **Ksh {estimated_value:,.2f}**")
else:
    st.info("Milk production data unavailable for valuation.")

# --- Data Filtering ---
st.header("🔍 Filter & Explore Data")

if 'Insemination Date' in df.columns:
    min_date = df['Insemination Date'].min()
    max_date = df['Insemination Date'].max()
    date_range = st.date_input("Filter by Insemination Date Range", [min_date, max_date])
    filtered_df = df[(df['Insemination Date'] >= pd.to_datetime(date_range[0])) &
                     (df['Insemination Date'] <= pd.to_datetime(date_range[1]))]
else:
    filtered_df = df.copy()

# --- Time Series Plots ---
st.header("📈 Time Series Plots")

numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()

for col in numeric_cols:
    if col in ['Cow ID', 'Tag Number']:  # Skip IDs for plotting
        continue
    st.subheader(f"{col} Over Time")
    if 'Insemination Date' in filtered_df.columns:
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.lineplot(data=filtered_df, x='Insemination Date', y=col, marker='o', ax=ax)
        ax.set_xlabel("Insemination Date")
        ax.set_ylabel(col)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.write(f"Cannot plot {col} - 'Insemination Date' missing.")

# --- Pie Charts for Categorical Variables ---
st.header("📊 Categorical Data Distributions")

categorical_cols = filtered_df.select_dtypes(include=['object']).columns.tolist()

for col in categorical_cols:
    st.subheader(f"{col} Distribution")
    counts = filtered_df[col].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140)
    ax.axis('equal')
    plt.tight_layout()
    st.pyplot(fig)

# --- Data Preview ---
st.header("📋 Data Preview")
st.dataframe(filtered_df)
