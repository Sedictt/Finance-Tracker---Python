import customtkinter as ctk;
import customtkinter as ctk
import sqlite3
import datetime
import os
import math
import statistics

from tkinter import ttk, messagebox, simpledialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats

# -------------------------
# Color Theme Constants
# -------------------------
COLOR_INCOME = "#2ecc71"
COLOR_EXPENSES = "#e74c3c"
COLOR_NET = "#3498db"
COLOR_COUNT = "#9b59b6"
COLOR_TEXT_WHITE = "white"
COLOR_BTN_SUCCESS = "#27ae60"
COLOR_BTN_DANGER = "#c0392b"
COLOR_HOVER_SUCCESS = "#2ecc71"
COLOR_HOVER_DANGER = "#e74c3c"

DB_FILE = "finance_ctk.db"

# -------------------------
# Database utilities
# -------------------------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        balance REAL DEFAULT 0
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        date TEXT,
        account_id INTEGER,
        amount REAL,
        category_id INTEGER,
        payee TEXT,
        note TEXT
    )""")
    conn.commit()
    conn.close()

def add_account_if_missing(name):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO accounts (name) VALUES (?)", (name,))
    conn.commit(); conn.close()

def add_category_if_missing(name):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit(); conn.close()

def insert_transaction(date, account_name, amount, category_name, payee="", note=""):
    add_account_if_missing(account_name)
    add_category_if_missing(category_name)
    conn = get_conn(); cur = conn.cursor()
    # get ids
    cur.execute("SELECT id FROM accounts WHERE name=?", (account_name,))
    acc_id = cur.fetchone()["id"]
    cur.execute("SELECT id FROM categories WHERE name=?", (category_name,))
    cat_id = cur.fetchone()["id"]
    cur.execute("""
        INSERT INTO transactions (date, account_id, amount, category_id, payee, note)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (date, acc_id, amount, cat_id, payee, note))
    # update account balance
    cur.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, acc_id))
    conn.commit(); conn.close()

def fetch_transactions(limit=500):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
    SELECT t.id, t.date, a.name as account, t.amount, c.name as category, t.payee, t.note
    FROM transactions t
    LEFT JOIN accounts a ON t.account_id = a.id
    LEFT JOIN categories c ON t.category_id = c.id
    ORDER BY date DESC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_summary():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT SUM(amount) as total FROM transactions WHERE amount>0")
    income = cur.fetchone()["total"] or 0.0
    cur.execute("SELECT SUM(ABS(amount)) as total_exp FROM transactions WHERE amount<0")
    expenses = cur.fetchone()["total_exp"] or 0.0
    cur.execute("SELECT COUNT(*) as cnt FROM transactions")
    cnt = cur.fetchone()["cnt"]
    conn.close()
    net = income - expenses
    return {"income": income, "expenses": expenses, "net": net, "count": cnt}

def fetch_category_breakdown(year=None, month=None):
    conn = get_conn(); cur = conn.cursor()
    q = """
    SELECT c.name as category, SUM(ABS(t.amount)) as total
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.amount < 0
    """
    params = []
    if year and month:
        start = datetime.date(year, month, 1)
        if month == 12:
            end = datetime.date(year+1, 1, 1)
        else:
            end = datetime.date(year, month+1, 1)
        q += " AND date >= ? AND date < ?"
        params = [start.isoformat(), end.isoformat()]
    q += " GROUP BY category ORDER BY total DESC"
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return {r["category"] or "Uncategorized": r["total"] for r in rows}

def clear_all_data():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM transactions")
    cur.execute("DELETE FROM accounts")
    cur.execute("DELETE FROM categories")
    conn.commit(); conn.close()

# -------------------------
# Sample data
# -------------------------
SAMPLE_TRANSACTIONS = [
    ("2025-10-01", "Salary Account", 3099.00, "Income", "Employer", "Monthly salary"),
    ("2025-10-02", "Checking", -45.50, "Food", "Cafe", ""),
    ("2025-10-05", "Checking", -150.00, "Utilities", "Electric Co", ""),
    ("2025-10-07", "Checking", -200.00, "Rent", "Landlord", ""),
    ("2025-10-08", "Checking", -75.48, "Transport", "Taxi", ""),
    ("2025-10-10", "Checking", -120.00, "Entertainment", "Cinema", ""),
    ("2025-10-12", "Savings", -50.00, "Savings", "Bank", "Monthly save"),
    ("2025-10-14", "Checking", -80.00, "Food", "Restaurant", ""),
    ("2025-10-18", "Checking", -30.00, "Food", "Takeout", ""),
    ("2025-10-20", "Checking", -60.00, "Transport", "Train", ""),
    ("2025-10-22", "Checking", -100.00, "Utilities", "Water Co", ""),
    ("2025-10-25", "Checking", -20.00, "Misc", "Stationery", "")
]

# -------------------------
# Dashboard View
# -------------------------
class DashboardView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Initialize database
        init_db()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(self, text="Dashboard Overview", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.label = ctk.CTkLabel(self, text="Dashboard View", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=20)

        # Example content
        self.info_label = ctk.CTkLabel(self, text="Welcome to your financial overview.")
        self.info_label.grid(row=1, column=0, padx=20, pady=10)
        # Cards frame
        cards_frame = ctk.CTkFrame(self)
        cards_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=12)
        cards_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.card_income = ctk.CTkFrame(cards_frame, fg_color=COLOR_INCOME)
        self.card_income.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        self.label_income_title = ctk.CTkLabel(self.card_income, text="Total Income", text_color=COLOR_TEXT_WHITE)
        self.label_income_title.pack(anchor="w", padx=12, pady=(8,0))
        self.label_income_val = ctk.CTkLabel(self.card_income, text="$0.00", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLOR_TEXT_WHITE)
        self.label_income_val.pack(anchor="w", padx=12, pady=(0,12))

        self.card_expenses = ctk.CTkFrame(cards_frame, fg_color=COLOR_EXPENSES)
        self.card_expenses.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        self.label_exp_title = ctk.CTkLabel(self.card_expenses, text="Total Expenses", text_color=COLOR_TEXT_WHITE)
        self.label_exp_title.pack(anchor="w", padx=12, pady=(8,0))
        self.label_exp_val = ctk.CTkLabel(self.card_expenses, text="$0.00", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLOR_TEXT_WHITE)
        self.label_exp_val.pack(anchor="w", padx=12, pady=(0,12))

        self.card_net = ctk.CTkFrame(cards_frame, fg_color=COLOR_NET)
        self.card_net.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")
        self.label_net_title = ctk.CTkLabel(self.card_net, text="Net Balance", text_color=COLOR_TEXT_WHITE)
        self.label_net_title.pack(anchor="w", padx=12, pady=(8,0))
        self.label_net_val = ctk.CTkLabel(self.card_net, text="$0.00", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLOR_TEXT_WHITE)
        self.label_net_val.pack(anchor="w", padx=12, pady=(0,12))

        self.card_count = ctk.CTkFrame(cards_frame, fg_color=COLOR_COUNT)
        self.card_count.grid(row=0, column=3, padx=6, pady=6, sticky="nsew")
        self.label_cnt_title = ctk.CTkLabel(self.card_count, text="Transaction Count", text_color=COLOR_TEXT_WHITE)
        self.label_cnt_title.pack(anchor="w", padx=12, pady=(8,0))
        self.label_cnt_val = ctk.CTkLabel(self.card_count, text="0", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLOR_TEXT_WHITE)
        self.label_cnt_val.pack(anchor="w", padx=12, pady=(0,12))

        # Quick actions
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=2, column=0, sticky="ew", padx=16)
        actions_frame.grid_columnconfigure((0,1,2,3), weight=1)

        btn_refresh = ctk.CTkButton(actions_frame, text="Refresh", command=self.update_all, width=120)
        btn_refresh.grid(row=0, column=0, padx=8, pady=12, sticky="w")
        
        btn_add_sample = ctk.CTkButton(actions_frame, text="Add Sample Data", fg_color=COLOR_BTN_SUCCESS, hover_color=COLOR_HOVER_SUCCESS, command=self.add_sample_data)
        btn_add_sample.grid(row=0, column=1, padx=8, pady=12, sticky="w")
        
        btn_clear = ctk.CTkButton(actions_frame, text="Clear All", fg_color=COLOR_BTN_DANGER, hover_color=COLOR_HOVER_DANGER, command=self.clear_all_confirm)
        btn_clear.grid(row=0, column=2, padx=8, pady=12, sticky="w")

        # Spending by category (pie)
        chart_frame = ctk.CTkFrame(self)
        chart_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(6,16))
        chart_frame.grid_rowconfigure(0, weight=1)
        chart_frame.grid_columnconfigure(0, weight=1)
        self.pie_container = chart_frame

        # Initial load
        self.update_all()

    def update_all(self):
        # Update cards
        s = fetch_summary()
        self.label_income_val.configure(text=f"${s['income']:.2f}")
        self.label_exp_val.configure(text=f"${s['expenses']:.2f}")
        self.label_net_val.configure(text=f"${s['net']:.2f}")
        self.label_cnt_val.configure(text=f"{s['count']}")

        # Update dashboard pie chart if container exists
        if hasattr(self, "pie_container"):
            self._draw_pie(self.pie_container)

    def add_sample_data(self):
        for t in SAMPLE_TRANSACTIONS:
            insert_transaction(*t)
        messagebox.showinfo("Sample Data", "Sample transactions added.")
        self.update_all()

    def clear_all_confirm(self):
        if messagebox.askyesno("Confirm", "This will delete ALL data. Continue?"):
            clear_all_data()
            init_db()
            messagebox.showinfo("Cleared", "All data removed.")
            self.update_all()

    def _draw_pie(self, container, year=None, month=None):
        # remove previous canvas if exists
        for w in container.winfo_children():
            w.destroy()

        breakdown = fetch_category_breakdown(year, month)
        labels = list(breakdown.keys())
        values = list(breakdown.values())
        if not values:
            lbl = ctk.CTkLabel(container, text="No expense data to show for pie chart.")
            lbl.pack(padx=12, pady=24)
            return

        fig = Figure(figsize=(5,4), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
        ax.axis("equal")
        ax.set_title("Spending by Category")

        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=6, pady=6)
        canvas.draw()
