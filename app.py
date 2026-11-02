import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
from groq import Groq

# Database Setup
DB_FILE = "expenses.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            description TEXT,
            expense_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="AI Expense Analyzer", layout="wide")
st.title("💰 AI Expense Analyzer Application")

# Sidebar for Groq API Key & Adding Expenses
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter Groq API Key", type="password")

st.sidebar.header("Add New Expense")
amount = st.sidebar.number_input("Amount", min_value=0.0, format="%.2f")
category = st.sidebar.selectbox("Category", ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Other"])
description = st.sidebar.text_area("Description")
expense_date = st.sidebar.date_input("Date")

if st.sidebar.button("Add Expense"):
    if amount > 0:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (amount, category, description, expense_date) VALUES (?, ?, ?, ?)",
                       (amount, category, description, str(expense_date)))
        conn.commit()
        conn.close()
        st.sidebar.success("Expense added successfully!")
    else:
        st.sidebar.error("Please enter a valid amount.")

# Fetch Data from Database
conn = sqlite3.connect(DB_FILE)
df = pd.read_sql("SELECT * FROM expenses", conn)
conn.close()

if not df.empty:
    st.subheader("📊 Expense Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Expenses", f"Rs. {df['amount'].sum():,.2f}")
    col2.metric("Total Transactions", len(df))
    col3.metric("Categories", df['category'].nunique())
    
    st.divider()

    # Charts Section
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Expenses by Category (Pie Chart)")
        fig_pie = px.pie(df, names='category', values='amount', hole=0.3)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        st.subheader("Expenses Bar Chart")
        fig_bar = px.bar(df, x='expense_date', y='amount', color='category')
        st.plotly_chart(fig_bar, use_container_width=True)

    # AI Analysis Section
    st.subheader("🤖 Groq AI Insights & Strategies")
    if st.button("Analyze My Expenses with AI"):
        if not api_key:
            st.warning("Please enter your Groq API Key in the sidebar first.")
        else:
            try:
                client = Groq(api_key=api_key)
                expense_summary = df.to_string(index=False)
                
                prompt = f"""
                Here are my expenses:
                {expense_summary}
                
                Please analyze the patterns of my expenses, identify when I spend too much, 
                and recommend various strategies to handle and reduce my expenses.
                """
                
                with st.spinner("AI is analyzing your spending patterns..."):
                    chat_completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    ai_response = chat_completion.choices[0].message.content
                    st.success("Analysis Complete!")
                    st.write(ai_response)
            except Exception as e:
                st.error(f"Error connecting to Groq: {e}")
                
    st.divider()
    st.subheader("🧾 Expense Records")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No expenses added yet. Please add some expenses using the sidebar.")
