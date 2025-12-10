# transaction/manager.py
import sqlite3
import collections
from collections import Counter, defaultdict, namedtuple
import datetime
import sys
import json
import math
from typing import Iterable, Iterator, List, Dict, Any

# Third-party imports (used later): numpy, matplotlib, scipy
import numpy as np  # numpy: Arrays, numerical ops, used for ML and statistics
import matplotlib.pyplot as plt  # matplotlib: plotting
from scipy import stats  # scipy: statistics (mode etc.)
import statistics as stats_stdlib  # mean/median/mode/stdev
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import messagebox


# -----------------------------
# Backwards-compatible TransactionView
# -----------------------------
try:
    import customtkinter as ctk

    class TransactionView(ctk.CTkFrame):
        """GUI Transaction view using CustomTkinter.

        This restores the original exported symbol so existing imports
        like `from transaction.manager import TransactionView` continue to work.
        """

        # Modern Palette to align with Dashboard
        COLOR_BG_CARD = "#2b2b2b"
        COLOR_PRIMARY = "#2B2D42"
        COLOR_SECONDARY = "#8D99AE"
        COLOR_ACCENT = "#D90429"
        
        COLOR_BTN_REFRESH = "#34495e"
        COLOR_BTN_ADD = "#27ae60"
        COLOR_BTN_DELETE = "#c0392b"
        COLOR_BTN_SELECT_ALL = "#2980b9"

        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
            init_db()
            
            # Embed check
            try:
                if master is not None and getattr(master, "__class__", None) and master.__class__.__name__ == "DashboardView":
                    self._embedded_in_dashboard = True
                    return
            except Exception:
                pass

            # Properties
            self._income_categories = ["Salary", "Allowance", "Freelance", "Business Income", "Investments", "Gifts", "Refunds", "Other Income"]
            self._expense_categories = ["Food", "Transportation", "Shopping", "Entertainment", "Bills & Utilities", "Health & Personal Care", "Education", "Debt Payments / Loans", "Savings & Investments", "Miscellaneous", "Others"]
            self._current_filter = None

            # Layout Configuration
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(3, weight=1) # The list takes the most space

            # --- 1. Header Section ---
            self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

            self.title_label = ctk.CTkLabel(self.header_frame, text="Transaction Management", 
                                          font=ctk.CTkFont(family="Roboto", size=24, weight="bold"))
            self.title_label.pack(side="left")

            self.subtitle = ctk.CTkLabel(self.header_frame, text="Manage your income and expenses efficiently.", 
                                       text_color=self.COLOR_SECONDARY, font=ctk.CTkFont(size=12))
            self.subtitle.pack(side="left", padx=10, pady=(5,0))

            # --- 2. Live Summary Stats ---
            self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.stats_frame.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
            self.stats_frame.grid_columnconfigure((0,1,2), weight=1) # Distribute evenly

            self.card_total_count = self.create_stat_card(self.stats_frame, "Total Transactions", "0", "#3498db", 0)
            self.card_total_income = self.create_stat_card(self.stats_frame, "Total Income", "₱0.00", "#27ae60", 1)
            self.card_total_expense = self.create_stat_card(self.stats_frame, "Total Expenses", "₱0.00", "#c0392b", 2)

            # --- 3. Controls & Filter Bar ---
            self.controls_frame = ctk.CTkFrame(self, fg_color=self.COLOR_BG_CARD, corner_radius=10)
            self.controls_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
            self.controls_frame.grid_columnconfigure(5, weight=1) # Spacer to push search/filter

            # Action Buttons
            self.btn_add = ctk.CTkButton(self.controls_frame, text="+ Add New", command=self._on_add, 
                                       fg_color=self.COLOR_BTN_ADD, height=32, corner_radius=16, font=ctk.CTkFont(weight="bold"))
            self.btn_add.grid(row=0, column=0, padx=10, pady=10)
            
            self.btn_delete = ctk.CTkButton(self.controls_frame, text="Delete Selected", command=self._on_delete, 
                                          fg_color=self.COLOR_BTN_DELETE, height=32, corner_radius=16, font=ctk.CTkFont(weight="bold"))
            self.btn_delete.grid(row=0, column=1, padx=(0, 10), pady=10)

            self.btn_refresh = ctk.CTkButton(self.controls_frame, text="Refresh", command=self._on_refresh, 
                                           fg_color=self.COLOR_BTN_REFRESH, height=32, corner_radius=16, width=80)
            self.btn_refresh.grid(row=0, column=2, padx=(0, 10), pady=10)
            
            self.btn_select_all = ctk.CTkButton(self.controls_frame, text="Select All", command=self._on_select_all, 
                                              fg_color=self.COLOR_BTN_SELECT_ALL, height=32, corner_radius=16, width=90)
            self.btn_select_all.grid(row=0, column=3, padx=(0, 10), pady=10)
            
            # Filter Label
            ctk.CTkLabel(self.controls_frame, text="Filter Category:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=5, sticky="e", padx=(10, 5))

            # Filter Combo
            self.var_filter = tk.StringVar(value="All Categories")
            self.combo_filter = ctk.CTkComboBox(self.controls_frame, values=["All Categories"], variable=self.var_filter,
                                              width=200, state="readonly", command=self._on_apply_filter)
            self.combo_filter.grid(row=0, column=6, sticky="e", padx=10, pady=10)

            # --- 4. Transaction List (Treeview) ---
            self.list_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=self.COLOR_BG_CARD)
            self.list_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")
            self.list_frame.grid_rowconfigure(0, weight=1)
            self.list_frame.grid_columnconfigure(0, weight=1)

            # Styling the Treeview
            style = ttk.Style()
            style.theme_use('clam')
            
            # Header Style
            style.configure("Treeview.Heading", 
                          background="#202020", 
                          foreground="#ffffff", 
                          relief="flat",
                          font=("Roboto", 14, "bold")) # Increased Font Size
            style.map("Treeview.Heading", background=[('active', '#303030')])
            
            # Cell Style
            style.configure("Treeview", 
                          background="#2b2b2b", 
                          fieldbackground="#2b2b2b", 
                          foreground="#ffffff", 
                          font=("Roboto", 12), # Increased Font Size
                          rowheight=35,        # Increased Row Height
                          borderwidth=0)
            style.map("Treeview", background=[('selected', '#3498db')])

            self.tree = ttk.Treeview(self.list_frame, 
                                   columns=("id","date","type","category","amount","description"), 
                                   show="headings", 
                                   style="Treeview",
                                   selectmode="extended")
            
            # Configure Columns
            cols = {
                "id": ("ID", 50, "center"),
                "date": ("Date", 120, "center"),
                "type": ("Type", 100, "center"),
                "category": ("Category", 180, "w"),
                "amount": ("Amount", 140, "e"),
                "description": ("Description", 350, "w")
            }
            
            for col, (text, width, anchor) in cols.items():
                self.tree.heading(col, text=text)
                self.tree.column(col, width=width, anchor=anchor)

            # Scrollbars
            vsb = ctk.CTkScrollbar(self.list_frame, orientation="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=vsb.set)
            
            self.tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            vsb.grid(row=0, column=1, sticky="ns", padx=(0,2), pady=2)

            self.tree.bind("<Double-Button-1>", self._on_tree_header_double_click)

            # Load Data
            self.load_table_from_db()

        def create_stat_card(self, parent, title, initial_value, accent_color, col_idx):
            card = ctk.CTkFrame(parent, fg_color=self.COLOR_BG_CARD, corner_radius=15)
            card.grid(row=0, column=col_idx, sticky="ew", padx=5)
            
            # Color Strip
            strip = ctk.CTkFrame(card, height=80, width=6, fg_color=accent_color, corner_radius=6)
            strip.pack(side="left", fill="y", padx=(0, 15))
            
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(side="left", fill="both", expand=True, pady=10)
            
            lbl_title = ctk.CTkLabel(content, text=title, font=ctk.CTkFont(family="Roboto", size=12, weight="bold"), text_color="gray70")
            lbl_title.pack(anchor="w")
            
            lbl_val = ctk.CTkLabel(content, text=initial_value, font=ctk.CTkFont(family="Roboto", size=22, weight="bold"), text_color="white")
            lbl_val.pack(anchor="w", pady=(0, 0))
            
            return lbl_val

        def _on_tree_header_double_click(self, event):
            region = self.tree.identify_region(event.x, event.y)
            column = self.tree.identify_column(event.x)
            if region != "heading": return
            
            try:
                col_idx = int(column[1:]) - 1
                col_name = self.tree.cget("columns")[col_idx]
            except Exception: return
            
            max_width = tkFont.Font().measure(self.tree.heading(col_name, "text"))
            for item in self.tree.get_children():
                try:
                    txt = str(self.tree.item(item, "values")[col_idx])
                    max_width = max(max_width, tkFont.Font().measure(txt))
                except: pass
            
            self.tree.column(col_name, width=max_width + 20)

        def load_table_from_db(self):
            try:
                txs = load_transactions_from_db()
            except Exception: return

            for iid in self.tree.get_children():
                self.tree.delete(iid)
                
            cats = set()
            
            # Summary counters
            count = 0
            total_inc = 0.0
            total_exp = 0.0
            
            for t in txs:
                # Type logic
                tx_type = "Income" if t.amount >= 0 else "Expense"
                
                # Filter Logic
                cats.add(t.category)
                if self._current_filter and self._current_filter != "All Categories":
                    if t.category != self._current_filter: continue
                
                # Stats calculation (based on filtered view)
                count += 1
                if t.amount >= 0: total_inc += t.amount
                else: total_exp += abs(t.amount)

                # Formatting
                amt_str = f"₱{abs(t.amount):,.2f}"
                if t.amount < 0:
                    amt_str = f"- {amt_str}"
                else: 
                     amt_str = f"+ {amt_str}"

                self.tree.insert("", "end", values=(t.id, t.date, tx_type, t.category, amt_str, t.description))

            # Update Stats Cards
            self.card_total_count.configure(text=str(count))
            self.card_total_income.configure(text=f"₱{total_inc:,.2f}")
            self.card_total_expense.configure(text=f"₱{total_exp:,.2f}")

            # Update combo
            values = ["All Categories"] + sorted(cats)
            self.combo_filter.configure(values=values)
            
            if self._current_filter not in values:
                 self.var_filter.set("All Categories")
                 self._current_filter = None

        def _on_refresh(self):
            self.load_table_from_db()

        def _on_select_all(self):
            all_items = self.tree.get_children()
            if len(self.tree.selection()) < len(all_items):
                self.tree.selection_set(all_items)
            else:
                self.tree.selection_remove(all_items)

        def _on_apply_filter(self, choice):
            self._current_filter = choice if choice != "All Categories" else None
            self.load_table_from_db()
            
        def _on_clear_filter(self):
            self.var_filter.set("All Categories")
            self._current_filter = None
            self.load_table_from_db()

        def _on_delete(self):
            sels = self.tree.selection()
            if not sels:
                messagebox.showinfo("Delete", "No transactions selected.")
                return

            ids = []
            for s in sels:
                try:
                    ids.append(int(self.tree.item(s, "values")[0]))
                except: pass
            
            if not ids: return
            
            if not messagebox.askyesno("Confirm", f"Delete {len(ids)} transactions?"):
                return

            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            for tid in ids:
                try: cur.execute("DELETE FROM transactions WHERE id = ?", (tid,))
                except: pass
            conn.commit()
            conn.close()
            self._on_refresh()

        def _next_id(self):
            init_db()
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT MAX(id) FROM transactions")
            r = cur.fetchone()
            conn.close()
            return (r[0] + 1) if (r and r[0] is not None) else 1

        def _on_add(self):
            top = ctk.CTkToplevel(self)
            top.title("Add Transaction")
            top.geometry("480x600")
            top.resizable(False, False)
            top.grab_set() 
            
            content = ctk.CTkFrame(top, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=30, pady=30)
            
            ctk.CTkLabel(content, text="New Transaction", font=ctk.CTkFont(family="Roboto", size=22, weight="bold")).pack(pady=(0, 20))

            def create_field(label_text, widget_class, **kwargs):
                ctk.CTkLabel(content, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(anchor="w", pady=(5,0))
                w = widget_class(content, height=35, **kwargs)
                w.pack(fill="x", pady=(0, 10))
                return w

            # Date
            ent_date = create_field("Date (YYYY-MM-DD)", ctk.CTkEntry, placeholder_text="YYYY-MM-DD")
            ent_date.insert(0, datetime.date.today().isoformat())
            
            # Type
            var_type = tk.StringVar(value="Income")
            combo_type = create_field("Type", ctk.CTkComboBox, values=["Income", "Expense"], variable=var_type, state="readonly")
            
            # Category
            var_cat = tk.StringVar(value="Salary")
            combo_cat = create_field("Category", ctk.CTkComboBox, values=self._income_categories, variable=var_cat)
            
            def _update_cats(choice):
                if choice == "Income":
                    combo_cat.configure(values=self._income_categories)
                    var_cat.set(self._income_categories[0])
                else:
                    combo_cat.configure(values=self._expense_categories)
                    var_cat.set(self._expense_categories[0])
            combo_type.configure(command=_update_cats)

            # Amount
            ent_amount = create_field("Amount (₱)", ctk.CTkEntry, placeholder_text="0.00")
            
            # Description
            ctk.CTkLabel(content, text="Description", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(anchor="w", pady=(5,0))
            ent_desc = ctk.CTkTextbox(content, height=80)
            ent_desc.pack(fill="x", pady=(0, 20))

            # Actions
            btn_frame = ctk.CTkFrame(content, fg_color="transparent")
            btn_frame.pack(fill="x", pady=10)
            
            def _submit():
                try:
                    d_str = ent_date.get().strip()
                    datetime.datetime.strptime(d_str, "%Y-%m-%d")
                    
                    amt_str = ent_amount.get().strip()
                    if not amt_str: raise ValueError("Amount missing")
                    amt = float(amt_str)
                    if var_type.get() == "Expense": amt = -abs(amt)
                    else: amt = abs(amt)
                    
                    cat = var_cat.get().strip()
                    desc = ent_desc.get("1.0", "end").strip()
                    
                    tx = Transaction(self._next_id(), d_str, desc, amt, cat)
                    save_transaction_db(tx)
                    
                    top.destroy()
                    self._on_refresh()
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, text_color="gray", command=top.destroy).pack(side="left", expand=True, padx=5, fill="x")
            ctk.CTkButton(btn_frame, text="Save Transaction", command=_submit, fg_color=self.COLOR_BTN_ADD).pack(side="right", expand=True, padx=5, fill="x")
except Exception:
    # Fallback placeholder so imports do not fail in environments without GUI libs.
    class TransactionView:
        """Placeholder TransactionView when `customtkinter` is not installed.

        This allows non-GUI code to import the name without raising ImportError.
        """

        def __init__(self, master=None, **kwargs):
            self.master = master
            self.kwargs = kwargs
            try:
                if master is not None and getattr(master, "__class__", None) and master.__class__.__name__ == "DashboardView":
                    self._embedded_in_dashboard = True
                    return
            except Exception:
                pass

        def render_text(self):
            return "TransactionView placeholder (customtkinter not installed)"

        def __repr__(self):
            return "<TransactionView placeholder>"
        # placeholder doesn't support UI actions
        def _on_add(self):
            raise RuntimeError("TransactionView placeholder: UI actions not available")

        def _on_delete(self):
            raise RuntimeError("TransactionView placeholder: UI actions not available")

        def _on_refresh(self):
            raise RuntimeError("TransactionView placeholder: UI actions not available")



# -----------------------------
# Data Model: Classes & Inheritance
# -----------------------------

class Transaction:
    """Base Transaction class

    Implements: Classes objects, __init__ and __str__, object methods, self parameter
    Inheritance will be shown with `Income` and `Expense` subclasses below.
    """

    def __init__(self, tid: int, date: str, description: str, amount: float, category: str = "General"):
        # Casting: ensure amount stored as float (Casting)
        self.id = int(tid)
        self.date = str(date)
        # Modifying strings: normalize whitespace and capitalization
        self.description = description.strip().title()
        self.amount = float(amount)
        self.category = category.strip().title()

    def __str__(self):
        # f-strings: used here
        return f"Transaction(id={self.id}, date={self.date}, desc='{self.description}', amount={self.amount:.2f}, category='{self.category}')"

    def to_dict(self) -> Dict[str, Any]:
        # Dictionary: convert object to dict (Dictionary)
        return {"id": self.id, "date": self.date, "description": self.description, "amount": self.amount, "category": self.category}


class Income(Transaction):
    """Child class demonstrating Inheritance and Parent-child class"""

    def __init__(self, tid, date, description, amount, source="Salary"):
        super().__init__(tid, date, description, amount, category="Income")
        self.source = source

    def __str__(self):
        return f"Income({self.id}, {self.date}, {self.description}, +{self.amount:.2f}, source={self.source})"


class Expense(Transaction):
    def __init__(self, tid, date, description, amount, merchant="Unknown"):
        super().__init__(tid, date, description, amount, category="Expense")
        self.merchant = merchant

    def __str__(self):
        return f"Expense({self.id}, {self.date}, {self.description}, -{self.amount:.2f}, merchant={self.merchant})"


# -----------------------------
# Iterable / Iterator: TransactionCollection
# -----------------------------

class TransactionCollection(Iterable):
    """Holds transactions and implements an iterator (Iterable and Iterator)."""

    def __init__(self, transactions: List[Transaction] = None):
        self._transactions = list(transactions) if transactions else []

    def add(self, tx: Transaction):
        self._transactions.append(tx)

    def __len__(self):
        return len(self._transactions)

    def __iter__(self) -> Iterator[Transaction]:
        # Iterable implemented; returns an iterator object
        return iter(self._transactions)

    def amounts(self) -> List[float]:
        return [t.amount for t in self._transactions]


# -----------------------------
# Database: simple SQLite wrapper
# -----------------------------

DB_PATH = "transactions.db"


def init_db(path: str = DB_PATH):
    """Create a tiny SQLite DB and transactions table (Database)."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT,
            description TEXT,
            amount REAL,
            category TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_transaction_db(tx: Transaction, path: str = DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO transactions (id, date, description, amount, category) VALUES (?, ?, ?, ?, ?)",
                (tx.id, tx.date, tx.description, tx.amount, tx.category))
    conn.commit()
    conn.close()


def load_transactions_from_db(path: str = DB_PATH) -> TransactionCollection:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT id, date, description, amount, category FROM transactions ORDER BY date")
    rows = cur.fetchall()
    conn.close()
    txs = TransactionCollection()
    for r in rows:
        tid, date, desc, amount, category = r
        txs.add(Transaction(tid, date, desc, amount, category))
    return txs


            


# -----------------------------
# Examples showing Collections: list, tuple, set, dict
# -----------------------------

# List example (List)
sample_list = [1, 2, 3]

# Tuple example (Tuple)
sample_tuple = ("a", "b", "c")

# Set example (Set)
sample_set = set(sample_list)

# Dictionary example (Dictionary)
sample_dict = {"one": 1, "two": 2}


# -----------------------------
# String formatting: f-strings, placeholders and modifiers
# -----------------------------

def format_examples(amount: float):
    # f-string (F strings)
    s1 = f"Amount: {amount:.2f}"
    # old-style placeholders and modifiers
    s2 = "Amount: %0.2f" % (amount,)
    # str.format modifiers
    s3 = "Amount: {:+0.2f}".format(amount)
    return s1, s2, s3


# -----------------------------
# Functional tools: lambda, map, filter
# -----------------------------

double = lambda x: x * 2  # Lambda


def filter_expenses(txs: Iterable[Transaction]) -> List[Transaction]:
    # Filter using a lambda and list comprehension (Loops + lambda)
    return list(filter(lambda t: t.amount < 0 or t.category.lower() == "expense", txs))


# -----------------------------
# Statistical functions: mean, median, mode, stdev
# -----------------------------

def compute_basic_stats(amounts: List[float]) -> Dict[str, float]:
    # Using Python stdlib and scipy for mode (Mean median mode standard deviation)
    if not amounts:
        return {}
    data = [float(a) for a in amounts]
    mean = stats_stdlib.mean(data)
    median = stats_stdlib.median(data)
    try:
        mode = stats_stdlib.mode(data)
    except Exception:
        # fallback to scipy mode
        mode = float(stats.mode(data).mode[0])
    stdev = stats_stdlib.stdev(data) if len(data) > 1 else 0.0
    return {"mean": mean, "median": median, "mode": mode, "stdev": stdev}


# -----------------------------
# Numpy arrays and simple ML: Linear Regression using numpy.polyfit
# -----------------------------

def linear_regression_predict(amounts: List[float], predict_steps: int = 1):
    # Arrays: convert to numpy array (Arrays)
    arr = np.array(amounts, dtype=float)
    if arr.size == 0:
        return []
    # Simple linear regression on index -> amount (Linear regression)
    x = np.arange(len(arr))
    # Handle constant array
    if np.all(arr == arr[0]):
        return [float(arr[0])] * predict_steps
    coeffs = np.polyfit(x, arr, deg=1)  # slope, intercept
    slope, intercept = coeffs[0], coeffs[1]
    preds = []
    for i in range(len(arr), len(arr) + predict_steps):
        preds.append(float(slope * i + intercept))
    return preds


# -----------------------------
# Visualization: Matplotlib example
# -----------------------------

def plot_amounts(amounts: List[float], title: str = "Transaction Amounts"):
    if not amounts:
        return
    plt.figure(figsize=(6, 3))
    plt.plot(amounts, marker="o")
    plt.title(title)
    plt.xlabel("Index")
    plt.ylabel("Amount")
    plt.grid(True)
    # Save plot to file instead of showing (safer for non-interactive environments)
    plt.tight_layout()
    plt.savefig("amounts_plot.png")
    plt.close()


# -----------------------------
# Machine learning note: we used numpy.polyfit above (no sklearn required)
# -----------------------------


# -----------------------------
# Demonstration / CLI: User input, loops, if-else
# -----------------------------

def demo_interactive():
    """Interactively add a transaction (User input). If not interactive, load sample data."""
    init_db()
    collection = TransactionCollection()

    # Pre-populate with some sample transactions (List, Tuple used earlier)
    sample_data = [
        Transaction(1, "2025-01-01", "Opening Balance", 1000.0, "Income"),
        Transaction(2, "2025-01-05", "Coffee", -3.5, "Expense"),
        Transaction(3, "2025-01-07", "Groceries", -45.2, "Expense"),
        Transaction(4, "2025-01-10", "Salary", 2000.0, "Income"),
    ]
    for t in sample_data:
        collection.add(t)
        save_transaction_db(t)

    # Try to prompt the user; avoid blocking in non-interactive environments
    try:
        if sys.stdin.isatty():
            # User input: ask to add transaction (User input)
            raw = input("Add transaction as CSV (id,date,desc,amount,category) or press Enter to skip: ")
            if raw.strip():
                parts = [p.strip() for p in raw.split(",")]
                if len(parts) >= 5:
                    tid, date, desc, amount, category = parts[:5]
                    tx = Transaction(int(tid), date, desc, float(amount), category)
                    collection.add(tx)
                    save_transaction_db(tx)
                    print("Added:", tx)
                else:
                    print("Not enough parts; skipping.")
        else:
            # Non-interactive: log note
            print("Non-interactive environment detected; using sample data.")
    except Exception as e:
        print("Input skipped (non-interactive or error):", e)

    # Loops + if-else: summarize expenses vs income
    total_income = 0.0
    total_expense = 0.0
    for t in collection:
        if t.category.lower() == "income" or t.amount > 0:
            total_income += t.amount
        else:
            total_expense += t.amount

    # Placeholders and modifiers example
    s1, s2, s3 = format_examples(total_income)
    print("Summary:")
    print(f"Total income: {total_income:.2f}")
    print(s2)  # old-style modifier usage shown

    # Iterators and iterables used when calling list(collection)
    amounts = collection.amounts()

    # Numpy, stats and ML usage
    stats_result = compute_basic_stats(amounts)
    print("Stats:", stats_result)
    preds = linear_regression_predict(amounts, predict_steps=3)
    print("Next predictions:", preds)

    # Plot and save
    plot_amounts(amounts)

    # More functional examples: map + lambda
    doubles = list(map(double, amounts))
    print("Doubled amounts:", doubles)

    # Collections example: Counter
    cat_counter = Counter([t.category for t in collection])
    print("Category counts:", dict(cat_counter))

    # Return collection for possible programmatic use
    return collection


if __name__ == "__main__":
    # Quick demonstration run when executed directly
    demo_interactive()

