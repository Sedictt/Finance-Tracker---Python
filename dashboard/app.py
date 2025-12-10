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

DB_FILE = "transactions.db"

# -------------------------
# Sample Data
# -------------------------
SAMPLE_TRANSACTIONS = [
    (datetime.date.today().isoformat(), "Salary", 5000.0, "Salary"),
    (datetime.date.today().isoformat(), "Groceries", -3500.0, "Food"),
    (datetime.date.today().isoformat(), "Gas", -1200.0, "Transportation"),
    (datetime.date.today().isoformat(), "Internet Bill", -1800.0, "Bills & Utilities"),
    (datetime.date.today().isoformat(), "Freelance Project", 2500.0, "Freelance"),
    (datetime.date.today().isoformat(), "Coffee", -180.0, "Food"),
]

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
    # Simplified schema matching TransactionView
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        date TEXT,
        description TEXT,
        amount REAL,
        category TEXT
    )""")
    conn.commit()
    conn.close()

# Helper methods for adding data not strictly needed if we use TransactionView's logic,
# but kept for compatibility if referenced elsewhere.
def insert_transaction(date, description, amount, category):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (date, description, amount, category)
        VALUES (?, ?, ?, ?)""",
        (date, description, amount, category))
    conn.commit(); conn.close()

def fetch_transactions(limit=50):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
    SELECT id, date, description, amount, category
    FROM transactions
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
    SELECT category, SUM(ABS(amount)) as total
    FROM transactions
    WHERE amount < 0
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
    conn.commit(); conn.close()

# -------------------------
# Sample data
# -------------------------


# -------------------------
# Dashboard View
# -------------------------
# -------------------------
# Modern Color Palette
# -------------------------
# Using a more sophisticated palette
COLOR_BG_CARD = "#2b2b2b"      # Darker card background
COLOR_PRIMARY = "#2B2D42"      # Dark Blue-ish
COLOR_SECONDARY = "#8D99AE"    # Grey-ish Blue
COLOR_ACCENT = "#D90429"       # Red Accent

# Gradient-like solid colors for cards
COLOR_CARD_INCOME = "#219150"    # Rich Green
COLOR_CARD_EXPENSE = "#c0392b"   # Rich Red
COLOR_CARD_NET = "#2980b9"       # Rich Blue
COLOR_CARD_COUNT = "#8e44ad"     # Rich Purple

COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#AAAAAA"

# -------------------------
# Dashboard View
# -------------------------
class DashboardView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Initialize database
        init_db()

        # Main Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        # Row 0: Header
        # Row 1: Summary Cards
        # Row 2: Charts & Recent Transactions (Split view)
        # Row 3: Actions
        self.grid_rowconfigure(2, weight=1) 
        
        # --- 1. Header ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Financial Overview", 
                                      font=ctk.CTkFont(family="Roboto", size=28, weight="bold"))
        self.title_label.pack(side="left")
        
        self.date_label = ctk.CTkLabel(self.header_frame, text=datetime.date.today().strftime("%B %d, %Y"),
                                     font=ctk.CTkFont(family="Roboto", size=14), text_color=COLOR_TEXT_SECONDARY)
        self.date_label.pack(side="right", anchor="s", pady=5)

        # --- 2. Summary Cards ---
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_income = self.create_summary_card(self.cards_frame, "Total Income", "₱0.00", COLOR_CARD_INCOME, 0)
        self.card_expenses = self.create_summary_card(self.cards_frame, "Total Expenses", "₱0.00", COLOR_CARD_EXPENSE, 1)
        self.card_net = self.create_summary_card(self.cards_frame, "Net Balance", "₱0.00", COLOR_CARD_NET, 2)
        self.card_count = self.create_summary_card(self.cards_frame, "Transactions", "0", COLOR_CARD_COUNT, 3)

        # --- 3. Main Content Area (Split) ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=2) # Chart area
        self.content_frame.grid_columnconfigure(1, weight=1) # Recent list
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Left: Analytics Preview (Pie Chart)
        self.chart_container = ctk.CTkFrame(self.content_frame, fg_color=COLOR_BG_CARD, corner_radius=15)
        self.chart_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.chart_title = ctk.CTkLabel(self.chart_container, text="Spending Distribution", 
                                      font=ctk.CTkFont(size=16, weight="bold"))
        self.chart_title.pack(pady=10)
        
        self.pie_frame = ctk.CTkFrame(self.chart_container, fg_color="transparent")
        self.pie_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Right: Recent Transactions
        self.recent_frame = ctk.CTkFrame(self.content_frame, fg_color=COLOR_BG_CARD, corner_radius=15)
        self.recent_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        self.recent_title = ctk.CTkLabel(self.recent_frame, text="Recent Activity", 
                                       font=ctk.CTkFont(size=16, weight="bold"))
        self.recent_title.pack(pady=10)
        
        self.recent_list = ctk.CTkScrollableFrame(self.recent_frame, fg_color="transparent")
        self.recent_list.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 4. Actions Footer ---
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        
        self.btn_refresh = ctk.CTkButton(self.actions_frame, text="Refresh Data", command=self.update_all, 
                                       width=120, height=35, corner_radius=18, fg_color="#34495e")
        self.btn_refresh.pack(side="left", padx=(0, 10))
        
        self.btn_clear = ctk.CTkButton(self.actions_frame, text="Clear Data", 
                                     command=self.clear_all_confirm,
                                     fg_color=COLOR_BTN_DANGER, hover_color=COLOR_HOVER_DANGER,
                                     width=120, height=35, corner_radius=18)
        self.btn_clear.pack(side="right")

        # Initial Load
        self.update_all()

    def create_summary_card(self, parent, title, value, color, col_idx):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=15)
        card.grid(row=0, column=col_idx, padx=10, sticky="ew")
        
        # Add a subtle "icon" or decoration (optional, simpler to just use text for now)
        label_title = ctk.CTkLabel(card, text=title, text_color="white", font=ctk.CTkFont(size=12))
        label_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        label_value = ctk.CTkLabel(card, text=value, text_color="white", font=ctk.CTkFont(size=22, weight="bold"))
        label_value.pack(anchor="w", padx=15, pady=(0, 15))
        
        return label_value # return the value label so we can update it later

    def update_all(self):
        # Update cards
        s = fetch_summary()
        self.card_income.configure(text=f"₱{s['income']:,.2f}")
        self.card_expenses.configure(text=f"₱{s['expenses']:,.2f}")
        self.card_net.configure(text=f"₱{s['net']:,.2f}")
        self.card_count.configure(text=f"{s['count']}")

        # Update Chart
        self._draw_pie(self.pie_frame)
        
        # Update Recent Transactions
        self._update_recent_list()

    def _update_recent_list(self):
        # Clear existing
        for widget in self.recent_list.winfo_children():
            widget.destroy()
            
        recent_txs = fetch_transactions(limit=10)
        
        if not recent_txs:
            ctk.CTkLabel(self.recent_list, text="No recent transactions", 
                       text_color=COLOR_TEXT_SECONDARY).pack(pady=20)
            return

        for tx in recent_txs:
            row = ctk.CTkFrame(self.recent_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            # Left: Date + Description
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", padx=5)
            
            # Using description as main label
            desc = tx["description"] if "description" in tx.keys() else "Unnamed"
            ctk.CTkLabel(info_frame, text=desc, 
                       font=ctk.CTkFont(weight="bold", size=13)).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=tx["date"], 
                       font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")

            # Right: Amount
            amt = tx["amount"]
            color = COLOR_INCOME if amt > 0 else COLOR_EXPENSES
            ctk.CTkLabel(row, text=f"₱{abs(amt):,.2f}", 
                       text_color=color, font=ctk.CTkFont(weight="bold")).pack(side="right", padx=5)
            
            # Separator
            ttk.Separator(self.recent_list, orient="horizontal").pack(fill="x", pady=2)



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
            lbl = ctk.CTkLabel(container, text="No expense data available.", text_color=COLOR_TEXT_SECONDARY)
            lbl.pack(expand=True)
            return

        # Setup dark theme plot
        fig = Figure(figsize=(5,4), dpi=100)
        fig.patch.set_facecolor(COLOR_BG_CARD) # Match container bg
        
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLOR_BG_CARD)
        
        # Donut Chart style
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140, 
                                        pctdistance=0.85, textprops=dict(color="white"))
        
        # Draw circle for donut
        centre_circle = matplotlib.patches.Circle((0,0),0.70,fc=COLOR_BG_CARD)
        fig.gca().add_artist(centre_circle)
        
        ax.axis("equal")

        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()
