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
# UI Application
# -------------------------
class FinanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Tracker")
        self.geometry("1000x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Top bar
        self.top_frame = ctk.CTkFrame(self, height=70)
        self.top_frame.pack(fill="x", side="top")

        self.title_label = ctk.CTkLabel(self.top_frame, text=" Personal Finance Tracker",
                                        font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left", padx=16, pady=12)

        # Tab view
        self.tabview = ctk.CTkTabview(self, width=980, height=580)
        self.tabview.pack(padx=12, pady=8, fill="both", expand=True)
        self.tabview.add("Dashboard")
        self.tabview.add("Add Transaction")
        self.tabview.add("Transactions")
        self.tabview.add("Analytics")
        self.tabview.add("Predictions")

        self._build_dashboard_tab()
        self._build_add_tab()
        self._build_transactions_tab()
        self._build_analytics_tab()
        self._build_predictions_tab()

        init_db()
        self.update_all()

        # ensure Dashboard is the active tab by default
        self.tabview.set("Dashboard")

    # -------------------------
    # Dashboard Tab
    # -------------------------
    def _build_dashboard_tab(self):
        tab = self.tabview.tab("Dashboard")
        tab.grid_columnconfigure(0, weight=1)

        # Cards frame
        cards_frame = ctk.CTkFrame(tab)
        cards_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=12)
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
        actions_frame = ctk.CTkFrame(tab)
        actions_frame.grid(row=1, column=0, sticky="ew", padx=16)
        actions_frame.grid_columnconfigure((0,1,2,3), weight=1)

        btn_refresh = ctk.CTkButton(actions_frame, text="Refresh", command=self.update_all, width=120)
        btn_refresh.grid(row=0, column=0, padx=8, pady=12, sticky="w")
        btn_transactions = ctk.CTkButton(actions_frame, text="Transactions", command=lambda: self.tabview.set("Transactions"))
        btn_transactions.grid(row=0, column=1, padx=8, pady=12, sticky="w")
        btn_add_sample = ctk.CTkButton(actions_frame, text="Add Sample Data", fg_color=COLOR_BTN_SUCCESS, hover_color=COLOR_HOVER_SUCCESS, command=self.add_sample_data)
        btn_add_sample.grid(row=0, column=2, padx=8, pady=12, sticky="w")
        btn_clear = ctk.CTkButton(actions_frame, text="Clear All", fg_color=COLOR_BTN_DANGER, hover_color=COLOR_HOVER_DANGER, command=self.clear_all_confirm)
        btn_clear.grid(row=0, column=3, padx=8, pady=12, sticky="w")

        # Spending by category (pie)
        chart_frame = ctk.CTkFrame(tab)
        chart_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6,16))
        chart_frame.grid_rowconfigure(0, weight=1)
        chart_frame.grid_columnconfigure(0, weight=1)
        self.pie_container = chart_frame

    # -------------------------
    # Add Transaction Tab
    # -------------------------
    def _build_add_tab(self):
        tab = self.tabview.tab("Add Transaction")
        # keep tab present but minimal — dashboard-only work in progress
        container = ctk.CTkFrame(tab)
        container.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(container, text="Add Transaction — not implemented (dashboard-only)", justify="center").pack(expand=True)

    # -------------------------
    # Transactions Tab
    # -------------------------
    def _build_transactions_tab(self):
        tab = self.tabview.tab("Transactions")
        container = ctk.CTkFrame(tab)
        container.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(container, text="Transactions — not implemented (dashboard-only)", justify="center").pack(expand=True)

    # -------------------------
    # Analytics Tab
    # -------------------------
    def _build_analytics_tab(self):
        tab = self.tabview.tab("Analytics")
        container = ctk.CTkFrame(tab)
        container.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(container, text="Analytics — not implemented (dashboard-only)", justify="center").pack(expand=True)

    # -------------------------
    # Predictions Tab
    # -------------------------
    def _build_predictions_tab(self):
        tab = self.tabview.tab("Predictions")
        container = ctk.CTkFrame(tab)
        container.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(container, text="Predictions — not implemented (dashboard-only)", justify="center").pack(expand=True)

    # -------------------------
    # Actions & UI Updaters
    # -------------------------
    def update_all(self):
        # Update cards
        s = fetch_summary()
        self.label_income_val.configure(text=f"${s['income']:.2f}")
        self.label_exp_val.configure(text=f"${s['expenses']:.2f}")
        self.label_net_val.configure(text=f"${s['net']:.2f}")
        self.label_cnt_val.configure(text=f"{s['count']}")

        # Update transactions list if the tree widget exists
        if hasattr(self, "tree") and isinstance(getattr(self, "tree"), ttk.Treeview):
            for r in self.tree.get_children():
                self.tree.delete(r)
            for row in fetch_transactions(500):
                self.tree.insert("", "end", values=(row["id"], row["date"], row["account"], f"{row['amount']:.2f}", row["category"], row["payee"], row["note"]))

        # Update dashboard pie chart if container exists
        if hasattr(self, "pie_container"):
            self._draw_pie(self.pie_container)

        # Update analytics if analytics widgets exist
        if hasattr(self, "stats_text") and hasattr(self, "analytics_chart_container"):
            self._update_analytics()

    def on_add_transaction(self):
        date = self.entry_date.get().strip() or datetime.date.today().isoformat()
        
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format.")
            return
        
        acct = self.entry_account.get().strip() or "Checking"
        try:
            amount = float(self.entry_amount.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a valid number for amount.")
            return
        cat = self.entry_category.get().strip() or "Misc"
        payee = self.entry_payee.get().strip()
        note = self.entry_note.get().strip()

        insert_transaction(date, acct, amount, cat, payee, note)
        messagebox.showinfo("Added", "Transaction added.")
        # clear form
        self.entry_amount.delete(0, "end")
        self.entry_payee.delete(0, "end")
        self.entry_note.delete(0, "end")
        self.update_all()
        self.tabview.set("Dashboard")

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

    # -------------------------
    # Charts
    # -------------------------
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

    def _update_analytics(self):
        # basic stats to left panel
        rows = fetch_transactions(1000)
        amounts = [r["amount"] for r in rows]
        incomes = [a for a in amounts if a > 0]
        expenses = [-a for a in amounts if a < 0]

        stats_lines = []
        stats_lines.append(f"Total transactions: {len(amounts)}")
        stats_lines.append(f"Total income: ${sum(incomes):.2f}")
        stats_lines.append(f"Total expenses: ${sum(expenses):.2f}")
        if expenses:
            stats_lines.append(f"Avg expense: ${statistics.mean(expenses):.2f}")
            stats_lines.append(f"Median expense: ${statistics.median(expenses):.2f}")
            try:
                mode_val = stats.mode(expenses, keepdims=True).mode[0]
                stats_lines.append(f"Mode expense: ${mode_val:.2f}")
            except Exception:
                stats_lines.append(f"Mode expense: n/a")
            stats_lines.append(f"Std dev (expenses): ${statistics.pstdev(expenses):.2f}")
        self.stats_text.configure(text="\n".join(stats_lines))

        # update analytics pie
        self._draw_pie(self.analytics_chart_container)

    # -------------------------
    # Prediction
    # -------------------------
    def run_prediction(self):
        rows = fetch_transactions(500)
        # use absolute values of recent expenses (negative amounts)
        recent_expenses = [abs(r["amount"]) for r in reversed(rows) if r["amount"] < 0]  # chronological
        if len(recent_expenses) < 3:
            self.pred_label.configure(text="Not enough expense history (need at least 3 expenses).")
            return

        # use simple linear regression over expense index -> amount
        X = np.arange(len(recent_expenses)).reshape(-1,1)
        y = np.array(recent_expenses)
        model = LinearRegression()
        model.fit(X, y)
        next_idx = np.array([[len(recent_expenses)]])
        pred = model.predict(next_idx)[0]
        # clamp prediction
        pred = max(0.0, float(pred))
        trend = "increasing" if model.coef_[0] > 0 else "decreasing" if model.coef_[0] < 0 else "flat"
        self.pred_label.configure(text=f"Predicted next expense: ${pred:.2f}  (trend: {trend})")

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    init_db()
    app = FinanceApp()
    app.mainloop()

