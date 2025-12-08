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

        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
            # Initialize database on first use
            init_db()
            # If instantiated directly inside the Dashboard (we previously
            # injected TransactionView into `DashboardView`), skip building
            # the full UI so the Dashboard does not show the transactions
            # area inline. We detect by class name to avoid importing dashboard.
            try:
                if master is not None and getattr(master, "__class__", None) and master.__class__.__name__ == "DashboardView":
                    # mark as embedded and don't build widgets
                    self._embedded_in_dashboard = True
                    return
            except Exception:
                pass
            # Make the frame layout expand properly when placed in the main app
            self.grid_columnconfigure(0, weight=1)
            # list_frame will be placed at row 2 below header and intro
            self.grid_rowconfigure(2, weight=1)

            self.label = ctk.CTkLabel(self, text="Transaction Management", font=ctk.CTkFont(size=24, weight="bold"))
            self.label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

            # Example content (kept minimal to remain a lightweight component)
            # Intro subtitle under the main header
            self.subtitle = ctk.CTkLabel(self, text="View, filter and manage your transactions", font=ctk.CTkFont(size=12))
            self.subtitle.grid(row=1, column=0, padx=20, pady=(0,8), sticky="w")

            # single Add button is available in the controls below; remove redundant top-level add button

            # Define common categories for use in Add modal and Filter dropdown
            self._income_categories = ["Salary", "Allowance", "Freelance", "Business Income", "Investments", "Gifts", "Refunds", "Other Income"]
            self._expense_categories = ["Food", "Transportation", "Shopping", "Entertainment", "Bills & Utilities", "Health & Personal Care", "Education", "Debt Payments / Loans", "Savings & Investments", "Miscellaneous", "Others"]
            # Current active category filter (None means show all)
            self._current_filter = None

            # Create a visible area that lists some transactions so the tab isn't blank
            # Use a CTkFrame as container and place a ttk.Treeview for a proper table
            self.list_frame = ctk.CTkFrame(self, corner_radius=8)
            self.list_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
            # Configure list_frame to expand with parent; only the table row (2)
            # should expand. Keep control rows compact.
            self.list_frame.grid_columnconfigure(0, weight=1)
            self.list_frame.grid_rowconfigure(1, weight=0)

            # Top controls: Add / Delete / Refresh
            controls = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            # give slightly larger bottom padding so filter row sits further below
            controls.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 12))
            # Keep control buttons compact (don't stretch them across the row)
            controls.grid_columnconfigure((0,1,2,3), weight=0)
            controls.grid_rowconfigure(0, weight=0)

            self.btn_add = ctk.CTkButton(controls, text="Add", width=80, command=self._on_add)
            self.btn_add.grid(row=0, column=0, sticky="w", padx=(0,12))
            self.btn_delete = ctk.CTkButton(controls, text="Delete", width=80, command=self._on_delete)
            self.btn_delete.grid(row=0, column=1, sticky="w", padx=(0,12))
            self.btn_refresh = ctk.CTkButton(controls, text="Refresh", width=80, command=self._on_refresh)
            self.btn_refresh.grid(row=0, column=2, sticky="w", padx=(0,12))
            # Select All / Clear selection button to support multi-delete workflows
            self.btn_select_all = ctk.CTkButton(controls, text="Select All", width=100, command=self._on_select_all)
            self.btn_select_all.grid(row=0, column=3, sticky="e", padx=(0,6))

            # Filter controls (placed below main controls)
            # Set a small fixed height and disable geometry propagation so the
            # frame doesn't become too tall in some themes/environment.
            filter_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent", height=40)
            # increase top padding so there's a clear gap from the controls
            filter_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=(12,6))
            # Prevent children from changing the frame height
            try:
                filter_frame.grid_propagate(False)
            except Exception:
                # If CTkFrame does not implement grid_propagate, ignore silently
                pass
            filter_frame.grid_columnconfigure((0,1,2,3), weight=0)

            lbl_filter = ctk.CTkLabel(filter_frame, text="Category Filter:", font=ctk.CTkFont(weight="bold"))
            lbl_filter.grid(row=0, column=0, padx=(2,6), sticky="w")

            # Combobox for categories; values will be updated when loading DB
            self.var_filter = tk.StringVar(value="All Categories")
            self.combo_filter = ctk.CTkComboBox(filter_frame, values=["All Categories"], variable=self.var_filter, state="readonly", width=220)
            self.combo_filter.grid(row=0, column=1, padx=(0,6), sticky="w")

            self.btn_apply_filter = ctk.CTkButton(filter_frame, text="Apply", width=80, command=self._on_apply_filter)
            self.btn_apply_filter.grid(row=0, column=2, sticky="w", padx=(0,6))
            self.btn_clear_filter = ctk.CTkButton(filter_frame, text="Clear", width=80, command=self._on_clear_filter)
            self.btn_clear_filter.grid(row=0, column=3, sticky="w")

            # Table area
            table_container = ctk.CTkFrame(self.list_frame)
            table_container.grid(row=2, column=0, sticky="nsew", padx=6, pady=6)
            table_container.grid_rowconfigure(0, weight=1)
            table_container.grid_columnconfigure(0, weight=1)

            # Create a style for dark table header
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("Treeview.Heading", background="#2b2b2b", foreground="#ffffff", relief="flat")
            style.map("Treeview.Heading", background=[('active', '#404040')])
            
            # Create a standard ttk.Treeview to display tabular data with all columns
            # Allow extended selection so users can select multiple rows for deletion
            self.tree = ttk.Treeview(table_container, columns=("id","date","type","category","amount","description"), show="headings", height=20, style="Treeview", selectmode="extended")
            self.tree.heading("id", text="ID")
            self.tree.heading("date", text="Date")
            self.tree.heading("type", text="Type")
            self.tree.heading("category", text="Category")
            self.tree.heading("amount", text="Amount")
            self.tree.heading("description", text="Description")
            # Set column widths to span full table width with responsive layout
            self.tree.column("id", width=60, anchor="center", stretch=False)
            self.tree.column("date", width=100, anchor="center", stretch=False)
            self.tree.column("type", width=80, anchor="center", stretch=False)
            self.tree.column("category", width=100, anchor="center", stretch=False)
            self.tree.column("amount", width=100, anchor="e", stretch=False)
            self.tree.column("description", width=1, anchor="w", stretch=True)  # width=1 allows full expansion

            # Vertical scrollbar
            vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=vsb.set)
            self.tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")

            # Bind double-click on heading separator to auto-fit columns
            self.tree.bind("<Double-Button-1>", self._on_tree_header_double_click)

            # Load initial data from DB
            try:
                self.load_table_from_db()
            except Exception:
                # If DB missing or empty, show sample rows
                sample_txs = [(1, "2025-01-01", "Income", "Salary", 1000.0, "Opening Balance"), 
                              (2, "2025-01-05", "Expense", "Food", -3.5, "Coffee")]
                for r in sample_txs:
                    self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], f"{r[4]:+.2f}", r[5]))

            # Make tree expand (table is at row 2 after adding filter row)
            self.list_frame.grid_rowconfigure(2, weight=1)

        def _on_tree_header_double_click(self, event):
            """Auto-fit column width when double-clicking on header separator."""
            # Get the region (part of header where click occurred)
            region = self.tree.identify_region(event.x, event.y)
            column = self.tree.identify_column(event.x)
            
            # Only process if click is on a column header separator
            if region != "heading":
                return
            
            # Get the column index (convert from "#1" format to integer)
            try:
                col_idx = int(column[1:]) - 1
                columns = self.tree.cget("columns")
                if col_idx < 0 or col_idx >= len(columns):
                    return
                col_name = columns[col_idx]
            except (ValueError, IndexError):
                return
            
            # Calculate required width based on content
            max_width = tkFont.Font().measure(self.tree.heading(col_name, "text"))
            
            for item in self.tree.get_children():
                try:
                    item_text = str(self.tree.item(item, "values")[col_idx])
                    item_width = tkFont.Font().measure(item_text)
                    max_width = max(max_width, item_width)
                except (IndexError, ValueError):
                    pass
            
            # Add padding and set the column width
            new_width = max_width + 20
            self.tree.column(col_name, width=new_width)

        def load_table_from_db(self):
            """Load rows from the SQLite DB into the Treeview."""
            try:
                txs = load_transactions_from_db()
            except Exception:
                return
            # clear
            for iid in self.tree.get_children():
                self.tree.delete(iid)
            # gather categories to populate the filter dropdown
            cats = set()
            for t in txs:
                try:
                    amt = f"{t.amount:+.2f}"
                except Exception:
                    amt = str(t.amount)
                # Derive type from amount: positive = Income, negative = Expense
                tx_type = "Income" if t.amount >= 0 else "Expense"
                cats.add(t.category)
                # Apply active filter if set on the view
                if getattr(self, "_current_filter", None) and self._current_filter != "All Categories":
                    try:
                        if t.category != self._current_filter:
                            continue
                    except Exception:
                        pass
                self.tree.insert("", "end", values=(t.id, t.date, tx_type, t.category, amt, t.description))
            # update the filter combobox values to reflect categories in the DB
            try:
                values = ["All Categories"] + sorted(cats)
                if hasattr(self, "combo_filter"):
                    self.combo_filter.configure(values=values)
                    cur = self.var_filter.get() if hasattr(self, "var_filter") else None
                    if cur not in values:
                        self.var_filter.set("All Categories")
                        self._current_filter = None
            except Exception:
                pass

        def _on_refresh(self):
            self.load_table_from_db()

        def _on_select_all(self):
            """Toggle select all / clear selection for the Treeview."""
            all_items = self.tree.get_children()
            current = set(self.tree.selection())
            if not current or len(current) < len(all_items):
                # select everything
                self.tree.selection_set(all_items)
            else:
                # clear selection
                self.tree.selection_remove(all_items)

        def _on_apply_filter(self):
            """Apply the category filter selected in the combobox."""
            try:
                sel = self.var_filter.get() if hasattr(self, "var_filter") else None
                if not sel or sel == "All Categories":
                    self._current_filter = None
                else:
                    self._current_filter = sel
            except Exception:
                self._current_filter = None
            self.load_table_from_db()

        def _on_clear_filter(self):
            """Clear any active filter and reset the combobox to All Categories."""
            try:
                if hasattr(self, "var_filter"):
                    self.var_filter.set("All Categories")
                self._current_filter = None
            except Exception:
                self._current_filter = None
            self.load_table_from_db()

        def _on_delete(self):
            """Delete selected transactions after user confirmation."""
            sels = self.tree.selection()
            if not sels:
                # Nothing selected — show an informative message
                try:
                    messagebox.showinfo("Delete Transactions", "No transactions selected to delete.")
                except Exception:
                    pass
                return

            # Collect selected IDs and a short preview for confirmation
            ids = []
            previews = []
            for s in sels:
                vals = self.tree.item(s, "values")
                if not vals:
                    continue
                try:
                    tid = int(vals[0])
                    ids.append(tid)
                    previews.append(f"{tid}: {vals[1]} {vals[4]}")
                except Exception:
                    continue

            if not ids:
                return

            # Build a concise confirmation message
            msg = f"Delete {len(ids)} selected transaction(s)?\n"
            # show up to 6 previews, then indicate more if present
            sample = "\n".join(previews[:6])
            if sample:
                msg += "\n" + sample
            if len(previews) > 6:
                msg += f"\n...and {len(previews)-6} more"

            try:
                confirm = messagebox.askyesno("Confirm Delete", msg)
            except Exception:
                # In headless or non-standard environments fall back to yes
                confirm = True

            if not confirm:
                return

            # Perform deletion in DB
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            for tid in ids:
                try:
                    cur.execute("DELETE FROM transactions WHERE id = ?", (tid,))
                except Exception:
                    continue
            conn.commit()
            conn.close()
            self._on_refresh()

        def _next_id(self):
            # Ensure DB is initialized
            init_db()
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT MAX(id) FROM transactions")
            r = cur.fetchone()
            conn.close()
            if not r or r[0] is None:
                return 1
            return int(r[0]) + 1

        def _on_add(self):
            # modal dialog to add a transaction with proper inputs
            top = ctk.CTkToplevel(self)
            top.title("Add Transaction")
            top.geometry("520x380")
            top.resizable(False, False)
            
            # Define categories by type
            income_categories = ["Salary", "Allowance", "Freelance", "Business Income", "Investments", "Gifts", "Refunds", "Other Income"]
            expense_categories = ["Food", "Transportation", "Shopping", "Entertainment", "Bills & Utilities", "Health & Personal Care", "Education", "Debt Payments / Loans", "Savings & Investments", "Miscellaneous", "Others"]
            
            # default id and date
            nid = self._next_id()
            
            # Row 0: ID (read-only)
            lbl_id = ctk.CTkLabel(top, text="ID:", font=ctk.CTkFont(weight="bold"))
            lbl_id.grid(row=0, column=0, padx=12, pady=10, sticky="w")
            lbl_id_value = ctk.CTkLabel(top, text=str(nid), text_color="gray")
            lbl_id_value.grid(row=0, column=1, padx=6, pady=10, sticky="w")

            # Row 1: Date
            lbl_date = ctk.CTkLabel(top, text="Date (YYYY-MM-DD):", font=ctk.CTkFont(weight="bold"))
            lbl_date.grid(row=1, column=0, padx=12, pady=10, sticky="w")
            ent_date = ctk.CTkEntry(top, width=200)
            ent_date.insert(0, datetime.date.today().isoformat())
            ent_date.grid(row=1, column=1, padx=6, pady=10, sticky="w")

            # Row 2: Type (dropdown)
            lbl_type = ctk.CTkLabel(top, text="Type:", font=ctk.CTkFont(weight="bold"))
            lbl_type.grid(row=2, column=0, padx=12, pady=10, sticky="w")
            var_type = tk.StringVar(value="Income")
            combo_type = ctk.CTkComboBox(top, values=["Income", "Expense"], variable=var_type, state="readonly", width=200)
            combo_type.grid(row=2, column=1, padx=6, pady=10, sticky="w")

            # Row 3: Category (dropdown with categories based on type)
            lbl_cat = ctk.CTkLabel(top, text="Category:", font=ctk.CTkFont(weight="bold"))
            lbl_cat.grid(row=3, column=0, padx=12, pady=10, sticky="w")
            var_cat = tk.StringVar(value="Salary")
            combo_cat = ctk.CTkComboBox(top, values=income_categories, variable=var_cat, state="readonly", width=200)
            combo_cat.grid(row=3, column=1, padx=6, pady=10, sticky="w")
            
            # Function to update categories when type changes
            def _on_type_change(_):
                selected_type = var_type.get()
                if selected_type == "Income":
                    combo_cat.configure(values=income_categories)
                    var_cat.set(income_categories[0])  # Set to first income category
                else:  # Expense
                    combo_cat.configure(values=expense_categories)
                    var_cat.set(expense_categories[0])  # Set to first expense category
            
            combo_type.configure(command=_on_type_change)

            # Row 4: Amount (in Peso with 2 decimals)
            lbl_amount = ctk.CTkLabel(top, text="Amount (₱):", font=ctk.CTkFont(weight="bold"))
            lbl_amount.grid(row=4, column=0, padx=12, pady=10, sticky="w")
            ent_amount = ctk.CTkEntry(top, width=200, placeholder_text="0.00")
            ent_amount.grid(row=4, column=1, padx=6, pady=10, sticky="w")

            # Row 5: Description (optional)
            lbl_desc = ctk.CTkLabel(top, text="Description (Optional):", font=ctk.CTkFont(weight="bold"))
            lbl_desc.grid(row=5, column=0, padx=12, pady=10, sticky="nw")
            ent_desc = ctk.CTkTextbox(top, width=200, height=60)
            ent_desc.grid(row=5, column=1, padx=6, pady=10, sticky="nsew")

            # Row 6: Buttons (Cancel and Submit)
            def _submit():
                try:
                    date_str = ent_date.get().strip()
                    # Validate date format
                    try:
                        datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        try:
                            messagebox.showerror("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
                            ent_date.focus_set()
                        except Exception:
                            pass
                        return

                    tx_type = var_type.get().strip() or "Income"
                    category = var_cat.get().strip() or "Food"

                    # Parse and validate amount (2 decimal places)
                    amount_str = ent_amount.get().strip()
                    if not amount_str:
                        try:
                            messagebox.showerror("Amount Required", "Amount is required. Please enter a numeric value.")
                            ent_amount.focus_set()
                        except Exception:
                            pass
                        return
                    try:
                        amount = float(amount_str)
                        amount = round(amount, 2)
                        # Make negative if Expense
                        if tx_type == "Expense" and amount > 0:
                            amount = -amount
                    except ValueError:
                        try:
                            messagebox.showerror("Invalid Amount", "Please enter a valid number for Amount (e.g. 1234.56).")
                            ent_amount.focus_set()
                        except Exception:
                            pass
                        return

                    desc = ent_desc.get("1.0", "end").strip()

                    # Create and save transaction
                    tx = Transaction(nid, date_str, desc, amount, category)
                    save_transaction_db(tx)
                    top.destroy()
                    self._on_refresh()
                except Exception as e:
                    try:
                        messagebox.showerror("Add Transaction Failed", f"Failed to add transaction: {e}")
                    except Exception:
                        print("Failed to add transaction:", e)

            def _cancel():
                top.destroy()

            btn_frame = ctk.CTkFrame(top, fg_color="transparent")
            btn_frame.grid(row=6, column=0, columnspan=2, pady=20)

            btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", command=_cancel, width=100)
            btn_cancel.grid(row=0, column=0, padx=6)
            btn_submit = ctk.CTkButton(btn_frame, text="Add Transaction", command=_submit, width=150)
            btn_submit.grid(row=0, column=1, padx=6)
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

