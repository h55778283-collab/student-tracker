import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Expense Tracker", layout="wide")

# ---------------- UI DESIGN ----------------
st.markdown("""
<style>

.stApp {
    background-color: #0b1220;
    color: #e5e7eb;
}

section[data-testid="stSidebar"] {
    background-color: #0f172a;
}

.stButton>button {
    background: linear-gradient(90deg, #22c55e, #16a34a);
    color: white;
    border-radius: 10px;
    height: 3em;
    font-weight: bold;
    width: 100%;
}

.card {
    background-color: #111827;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
}

@media only screen and (max-width: 768px) {
    .stApp {
        padding: 10px;
    }

    div[data-testid="stHorizontalBlock"] {
        flex-direction: column;
    }

    .stButton>button {
        height: 3.5em;
    }
}

</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    category TEXT,
    amount REAL,
    date TEXT
)
""")

conn.commit()

# ---------------- ADD DATA ----------------
st.title("💰 Personal Expense Tracker")

menu = st.radio("Navigation", ["Add Transaction", "Dashboard", "Analytics"], horizontal=True)

# ---------------- ADD TRANSACTION ----------------
if menu == "Add Transaction":

    type_ = st.selectbox("Type", ["Income", "Expense"])
    category = st.selectbox("Category", ["Food", "Bills", "Transport", "Study", "Entertainment", "Other"])
    amount = st.number_input("Amount", min_value=0.0)
    date = st.date_input("Date")

    if st.button("Add Transaction"):
        c.execute(
            "INSERT INTO expenses(type,category,amount,date) VALUES (?,?,?,?)",
            (type_, category, amount, str(date))
        )
        conn.commit()
        st.success("Added successfully!")

    df = pd.read_sql("SELECT * FROM expenses", conn)

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "📥 Download CSV",
            df.to_csv(index=False),
            file_name="expenses.csv"
        )

        uploaded = st.file_uploader("📤 Import CSV")
        if uploaded:
            new_df = pd.read_csv(uploaded)
            new_df.to_sql("expenses", conn, if_exists="append", index=False)
            st.success("Imported successfully!")

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":

    df = pd.read_sql("SELECT * FROM expenses", conn)

    if not df.empty:

        total_income = df[df["type"] == "Income"]["amount"].sum()
        total_expense = df[df["type"] == "Expense"]["amount"].sum()
        balance = total_income - total_expense

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Income", total_income)
        col2.metric("💸 Expenses", total_expense)
        col3.metric("📊 Balance", balance)

        if balance < 0:
            st.error("⚠ You are overspending!")

        st.markdown("---")

        # CATEGORY BREAKDOWN
        expense_df = df[df["type"] == "Expense"]

        if not expense_df.empty:
            fig = px.pie(expense_df, names="category", values="amount", title="Spending by Category")
            st.plotly_chart(fig, use_container_width=True)

        # TREND OVER TIME
        df["date"] = pd.to_datetime(df["date"])
        trend = df.groupby("date")["amount"].sum().reset_index()

        fig2 = px.line(trend, x="date", y="amount", title="Daily Cash Flow")
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("No data yet")

# ---------------- ANALYTICS ----------------
elif menu == "Analytics":

    df = pd.read_sql("SELECT * FROM expenses", conn)

    if not df.empty:

        st.subheader("📊 Smart Insights")

        expense_df = df[df["type"] == "Expense"]

        if not expense_df.empty:

            top_category = expense_df.groupby("category")["amount"].sum().idxmax()
            st.warning(f"⚠ You spend most on: {top_category}")

            avg_spending = expense_df["amount"].mean()

            if avg_spending > 500:
                st.error("⚠ High average spending detected")
            else:
                st.success("👍 Spending is under control")

        st.markdown("---")

        st.subheader("📈 Monthly Summary")

        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.to_period("M").astype(str)

        monthly = df.groupby("month")["amount"].sum().reset_index()

        fig = px.bar(monthly, x="month", y="amount", title="Monthly Spending")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No analytics available")