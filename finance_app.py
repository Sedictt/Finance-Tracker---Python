"""
Personal Finance Tracker - Desktop GUI Application
Demonstrates: Tkinter, Matplotlib visualization, User Input, Control Flow, F-strings
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

from finance_core import Transaction, Income, Expense, FinanceDatabase, TransactionIterator
from finance_analytics import FinanceAnalyzer


class FinanceTrackerApp(tk.Tk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.title("💰 Personal Finance Tracker")
        self.geometry("1300x750")

        # Global font defaults (family size style)
        self.option_add("*Font", "Segoe_UI 10")
        self.option_add("*TButton.Font", "Segoe_UI 10")
        self.option_add("*TLabel.Font", "Segoe_UI 10")
        
        # Modern color scheme
        self.colors = {
            'primary': '#2C3E50',      # Dark blue-grey
            'secondary': '#3498DB',    # Bright blue
            'success': '#27AE60',      # Green
            'danger': '#E74C3C',       # Red
            'warning': '#F39C12',      # Orange
            'light': '#ECF0F1',        # Light grey
            'dark': '#34495E',         # Dark grey
            'bg': '#F8F9FA',           # Background
            'card': '#FFFFFF'          # Card background
        }
        
        # Configure window
        self.configure(bg=self.colors['bg'])
        
        # Apply modern ttk styling
        self._apply_styles()
        
        # Initialize database and analyzer
        self.db = FinanceDatabase("finance_app.db")
        self.analyzer = FinanceAnalyzer()
        
        # Create header
        self._create_header()
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create tabs
        self._create_dashboard_tab()
        self._create_add_transaction_tab()
        self._create_view_transactions_tab()
        self._create_analytics_tab()
        self._create_predictions_tab()
        
        # Status bar
        self.status_bar = tk.Label(self, text="Ready", bd=0, relief=tk.FLAT, anchor=tk.W,
                                   bg=self.colors['primary'], fg='white', 
                                   font=('Segoe UI', 9), padx=10, pady=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load initial data
        self.refresh_dashboard()
        self.load_transactions()
    
    def _apply_styles(self):
        """Apply modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure notebook tabs with modern look
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=self.colors['light'],
                       foreground=self.colors['primary'],
                       padding=[25, 12],
                       font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['card']), ('active', '#E8E8E8')],
                 foreground=[('selected', self.colors['secondary'])],
                 expand=[('selected', [1, 1, 1, 0])])
        
        # Configure frames
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('Card.TFrame',
                   background=self.colors['card'],
                   relief='flat',
                   borderwidth=0)
        style.configure('Section.TFrame', background=self.colors['card'])
        
        # Configure labels with hierarchy
        style.configure('TLabel', background=self.colors['bg'], 
                       foreground=self.colors['dark'], font=('Segoe UI', 10))
        style.configure('Card.TLabel', background=self.colors['card'], 
                       foreground=self.colors['dark'], font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'),
                       foreground=self.colors['primary'])
        style.configure('Subtitle.TLabel', font=('Segoe UI', 13, 'bold'),
                       foreground=self.colors['secondary'])
        style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'),
                       foreground=self.colors['dark'])
        style.configure('Muted.TLabel', font=('Segoe UI', 9),
                       foreground='#7F8C8D')
        
        # Configure base button (secondary) with rounded look
        style.configure('TButton',
                   background=self.colors['light'],
                   foreground=self.colors['primary'],
                   borderwidth=0,
                   focuscolor='none',
                   padding=[16, 10],
                   font=('Segoe UI', 10))
        style.map('TButton',
             background=[('active', '#D5DBDB'), ('pressed', '#BDC3C7')])

        # Primary button - vibrant blue
        style.configure('Primary.TButton',
                   background=self.colors['secondary'],
                   foreground='white',
                   padding=[20, 10],
                   font=('Segoe UI', 10, 'bold'))
        style.map('Primary.TButton',
             background=[('active', '#2980B9'), ('pressed', self.colors['primary'])])
        
        # Success button (green)
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       padding=[18, 10],
                       font=('Segoe UI', 10, 'bold'))
        style.map('Success.TButton',
                 background=[('active', '#229954'), ('pressed', '#1E8449')])
        
        # Danger button (red)
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground='white',
                       padding=[18, 10],
                       font=('Segoe UI', 10, 'bold'))
        style.map('Danger.TButton',
                 background=[('active', '#C0392B'), ('pressed', '#A93226')])
        
        # Warning button (orange)
        style.configure('Warning.TButton',
                       background=self.colors['warning'],
                       foreground='white',
                       padding=[18, 10],
                       font=('Segoe UI', 10, 'bold'))
        style.map('Warning.TButton',
                 background=[('active', '#E67E22'), ('pressed', '#D35400')])
        
        # Configure entries and combobox with modern look
        style.configure('TEntry', fieldbackground='white', 
                       foreground=self.colors['dark'], padding=10,
                       font=('Segoe UI', 11))
        style.configure('TCombobox', fieldbackground='white',
                       foreground=self.colors['dark'],
                       arrowcolor=self.colors['secondary'],
                       padding=10, font=('Segoe UI', 11))
        style.map('TCombobox', fieldbackground=[('readonly', 'white')])
        
        # Configure spinbox
        style.configure('TSpinbox', fieldbackground='white',
                       foreground=self.colors['dark'], padding=10,
                       arrowcolor=self.colors['secondary'],
                       font=('Segoe UI', 11))
        
        # Configure labelframe with card-like appearance
        style.configure('TLabelframe', background=self.colors['card'],
                       borderwidth=0, relief='flat')
        style.configure('TLabelframe.Label', 
                       background=self.colors['card'],
                       foreground=self.colors['primary'],
                       font=('Segoe UI', 12, 'bold'),
                       padding=[10, 5])
        
        # Modern section frame
        style.configure('Section.TLabelframe', background=self.colors['card'],
                       borderwidth=0, relief='flat')
        style.configure('Section.TLabelframe.Label',
                       background=self.colors['card'],
                       foreground=self.colors['secondary'],
                       font=('Segoe UI', 11, 'bold'))
        
        # Configure treeview with zebra stripes support
        style.configure('Treeview',
                       background='white',
                       foreground=self.colors['dark'],
                       fieldbackground='white',
                       rowheight=35,
                       font=('Segoe UI', 10))
        style.configure('Treeview.Heading',
                       background=self.colors['primary'],
                       foreground='white',
                       relief='flat',
                       font=('Segoe UI', 10, 'bold'))
        style.map('Treeview',
                 background=[('selected', self.colors['secondary'])],
                 foreground=[('selected', 'white')])
    
    def _create_header(self):
        """Create application header"""
        header = tk.Frame(self, bg=self.colors['primary'], height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        # Title
        title = tk.Label(header, text="💰 Personal Finance Tracker",
                font=("Segoe UI", 20, "bold"),
                        bg=self.colors['primary'], fg='white')
        title.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Subtitle
        subtitle = tk.Label(header, text="Track, Analyze, and Predict Your Finances",
                   font=("Segoe UI", 10),
                           bg=self.colors['primary'], fg=self.colors['light'])
        subtitle.pack(side=tk.LEFT, padx=5, pady=15)
    
    def _create_dashboard_tab(self):
        """Dashboard with summary statistics"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Dashboard")
        
        # Main scrollable container
        canvas = tk.Canvas(tab, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Make the scrollable frame expand to canvas width
        def configure_scroll_region(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', configure_scroll_region)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Inner container with consistent padding
        container = tk.Frame(scrollable_frame, bg=self.colors['bg'], padx=25, pady=25)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Welcome section
        welcome_card = tk.Frame(container, bg=self.colors['secondary'], padx=30, pady=22)
        welcome_card.pack(fill=tk.X, pady=(0, 20))
        tk.Label(welcome_card, text="👋 Welcome to Your Financial Dashboard",
                font=('Segoe UI', 16, 'bold'), bg=self.colors['secondary'], fg='white').pack(anchor='w')
        tk.Label(welcome_card, text="Monitor your income, expenses, and financial health at a glance",
                font=('Segoe UI', 10), bg=self.colors['secondary'], fg='#D6EAF8').pack(anchor='w', pady=(5,0))
        
        # Stats cards row - use grid for equal sizing
        stats_container = tk.Frame(container, bg=self.colors['bg'])
        stats_container.pack(fill=tk.X, pady=(0, 20))
        
        # Configure grid columns to be equal
        for col in range(4):
            stats_container.grid_columnconfigure(col, weight=1, uniform="stats")
        
        self.summary_labels = {}
        labels_data = [
            ('Total Income', '💵', '#27AE60', '#D5F5E3'),
            ('Total Expenses', '💳', '#E74C3C', '#FADBD8'),
            ('Net Balance', '💰', '#3498DB', '#D6EAF8'),
            ('Transaction Count', '📝', '#9B59B6', '#E8DAEF')
        ]
        
        for i, (label, icon, color, light_color) in enumerate(labels_data):
            # Create colored card for each stat
            card = tk.Frame(stats_container, bg=color, padx=20, pady=18)
            card.grid(row=0, column=i, sticky='nsew', padx=(0 if i==0 else 6, 6 if i<3 else 0))
            
            # Top: Icon + label
            tk.Label(card, text=f"{icon} {label}", 
                    font=('Segoe UI', 10), bg=color, fg=light_color).pack(anchor='w')
            
            # Value (large)
            value_label = tk.Label(card, text="$0.00", 
                                  font=('Segoe UI', 22, 'bold'), bg=color, fg='white')
            value_label.pack(anchor='w', pady=(8, 0))
            self.summary_labels[label] = value_label
        
        # Quick actions section with card style
        actions_card = tk.Frame(container, bg=self.colors['card'], padx=30, pady=22)
        actions_card.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(actions_card, text="⚡ Quick Actions",
                font=('Segoe UI', 13, 'bold'), bg=self.colors['card'], fg=self.colors['primary']).pack(anchor='w')
        tk.Label(actions_card, text="Common tasks and shortcuts",
                font=('Segoe UI', 9), bg=self.colors['card'], fg='#7F8C8D').pack(anchor='w', pady=(2, 15))
        
        btn_frame = tk.Frame(actions_card, bg=self.colors['card'])
        btn_frame.pack(anchor='w')
        
        ttk.Button(btn_frame, text="🔄 Refresh", 
                  command=self.refresh_dashboard).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="📋 Transactions", 
                  command=lambda: self.notebook.select(2)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="➕ Add Sample Data", style='Success.TButton',
                  command=self.add_sample_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="🗑️ Clear All", style='Danger.TButton',
                  command=self.clear_all_data).pack(side=tk.LEFT)
        
        # Chart section with card style
        chart_card = tk.Frame(container, bg=self.colors['card'], padx=30, pady=22)
        chart_card.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(chart_card, text="📈 Spending by Category",
                font=('Segoe UI', 13, 'bold'), bg=self.colors['card'], fg=self.colors['primary']).pack(anchor='w')
        tk.Label(chart_card, text="Visual breakdown of your expenses",
                font=('Segoe UI', 9), bg=self.colors['card'], fg='#7F8C8D').pack(anchor='w', pady=(2, 15))
        
        self.dashboard_chart_frame = tk.Frame(chart_card, bg=self.colors['card'])
        self.dashboard_chart_frame.pack(fill=tk.BOTH, expand=True)
    
    def _create_add_transaction_tab(self):
        """Tab for adding new transactions - User Input"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="➕ Add Transaction")
        
        # Main container - centered
        main_container = tk.Frame(tab, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Center wrapper
        center_wrapper = tk.Frame(main_container, bg=self.colors['bg'])
        center_wrapper.place(relx=0.5, rely=0.5, anchor='center')
        
        # Form card with modern styling
        form_card = tk.Frame(center_wrapper, bg=self.colors['card'], padx=50, pady=40)
        form_card.pack()
        
        # Header inside card
        tk.Label(form_card, text="📝 New Transaction",
                font=('Segoe UI', 20, 'bold'), bg=self.colors['card'], fg=self.colors['primary']).pack(anchor='w')
        tk.Label(form_card, text="Record your income or expenses",
                font=('Segoe UI', 10), bg=self.colors['card'], fg='#7F8C8D').pack(anchor='w', pady=(5, 25))
        
        # Transaction type toggle buttons
        type_section = tk.Frame(form_card, bg=self.colors['card'])
        type_section.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(type_section, text="Type",
                font=('Segoe UI', 10), bg=self.colors['card'], fg='#7F8C8D').pack(anchor='w', pady=(0, 8))
        
        self.trans_type = tk.StringVar(value="Expense")
        type_btn_frame = tk.Frame(type_section, bg=self.colors['card'])
        type_btn_frame.pack(fill=tk.X)
        
        # Toggle-style buttons for income/expense
        self.income_btn = tk.Button(type_btn_frame, text="💵 Income", font=('Segoe UI', 11),
                                   bg=self.colors['light'], fg=self.colors['dark'],
                                   relief='flat', padx=30, pady=10, cursor='hand2',
                                   command=lambda: self._set_trans_type('Income'))
        self.income_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.expense_btn = tk.Button(type_btn_frame, text="💳 Expense", font=('Segoe UI', 11, 'bold'),
                                    bg=self.colors['danger'], fg='white',
                                    relief='flat', padx=30, pady=10, cursor='hand2',
                                    command=lambda: self._set_trans_type('Expense'))
        self.expense_btn.pack(side=tk.LEFT)
        
        # Form fields with modern input styling
        fields_frame = tk.Frame(form_card, bg=self.colors['card'])
        fields_frame.pack(fill=tk.X)
        
        # Amount field with currency
        self._create_modern_field(fields_frame, "Amount", 0)
        amount_wrapper = tk.Frame(fields_frame, bg='#F0F3F4', relief='flat', padx=12, pady=0)
        amount_wrapper.grid(row=0, column=1, sticky='ew', pady=8)
        tk.Label(amount_wrapper, text="$", font=('Segoe UI', 12, 'bold'),
                bg='#F0F3F4', fg=self.colors['primary']).pack(side=tk.LEFT)
        self.amount_entry = tk.Entry(amount_wrapper, font=('Segoe UI', 12), width=30,
                                     bg='#F0F3F4', fg=self.colors['dark'], relief='flat',
                                     insertbackground=self.colors['primary'])
        self.amount_entry.pack(side=tk.LEFT, pady=10, padx=(5, 0))
        
        # Category dropdown
        self._create_modern_field(fields_frame, "Category", 1)
        self.category_entry = ttk.Combobox(fields_frame, width=35, font=('Segoe UI', 11))
        self.category_entry['values'] = ['🍔 Food', '🚗 Transportation', '🎬 Entertainment', 
                                         '💡 Utilities', '💰 Salary', '📈 Investment', 
                                         '🏥 Healthcare', '🛒 Shopping', '📦 Other']
        self.category_entry.grid(row=1, column=1, sticky='ew', pady=8)
        
        # Description
        self._create_modern_field(fields_frame, "Description", 2)
        self.desc_entry = tk.Entry(fields_frame, font=('Segoe UI', 11), width=35,
                                   bg='#F0F3F4', fg=self.colors['dark'], relief='flat',
                                   insertbackground=self.colors['primary'])
        self.desc_entry.grid(row=2, column=1, sticky='ew', pady=8, ipady=10)
        
        # Date
        self._create_modern_field(fields_frame, "Date", 3)
        self.date_entry = tk.Entry(fields_frame, font=('Segoe UI', 11), width=35,
                                   bg='#F0F3F4', fg=self.colors['dark'], relief='flat',
                                   insertbackground=self.colors['primary'])
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=3, column=1, sticky='ew', pady=8, ipady=10)
        
        # Configure column weights
        fields_frame.grid_columnconfigure(1, weight=1)
        
        # Action buttons
        button_frame = tk.Frame(form_card, bg=self.colors['card'])
        button_frame.pack(fill=tk.X, pady=(30, 0))

        add_btn = tk.Button(button_frame, text="✅ Add Transaction", font=('Segoe UI', 11, 'bold'),
                           bg=self.colors['success'], fg='white', relief='flat',
                           padx=25, pady=12, cursor='hand2', command=self.add_transaction)
        add_btn.pack(side=tk.LEFT, padx=(0, 10))
        add_btn.bind('<Enter>', lambda e: add_btn.config(bg='#229954'))
        add_btn.bind('<Leave>', lambda e: add_btn.config(bg=self.colors['success']))
        
        clear_btn = tk.Button(button_frame, text="🔄 Clear", font=('Segoe UI', 11),
                             bg=self.colors['light'], fg=self.colors['dark'], relief='flat',
                             padx=25, pady=12, cursor='hand2', command=self.clear_form)
        clear_btn.pack(side=tk.LEFT)
        clear_btn.bind('<Enter>', lambda e: clear_btn.config(bg='#D5DBDB'))
        clear_btn.bind('<Leave>', lambda e: clear_btn.config(bg=self.colors['light']))
    
    def _set_trans_type(self, trans_type):
        """Toggle transaction type with visual feedback"""
        self.trans_type.set(trans_type)
        if trans_type == 'Income':
            self.income_btn.config(bg=self.colors['success'], fg='white', font=('Segoe UI', 11, 'bold'))
            self.expense_btn.config(bg=self.colors['light'], fg=self.colors['dark'], font=('Segoe UI', 11))
        else:
            self.expense_btn.config(bg=self.colors['danger'], fg='white', font=('Segoe UI', 11, 'bold'))
            self.income_btn.config(bg=self.colors['light'], fg=self.colors['dark'], font=('Segoe UI', 11))
    
    def _create_modern_field(self, parent, label, row):
        """Helper to create modern form field labels"""
        tk.Label(parent, text=label, font=('Segoe UI', 10),
                bg=self.colors['card'], fg='#7F8C8D').grid(
                    row=row, column=0, sticky='nw', pady=15, padx=(0, 25))
    
    def _create_form_field(self, parent, label, row):
        """Helper to create consistent form field labels"""
        tk.Label(parent, text=label, font=('Segoe UI', 11, 'bold'),
                bg=self.colors['card'], fg=self.colors['dark']).grid(
                    row=row, column=0, sticky=tk.W, pady=12, padx=(0, 20))
    
    def _create_view_transactions_tab(self):
        """Tab for viewing all transactions"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Transactions")
        
        # Main container
        main_container = ttk.Frame(tab)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header card
        header_card = tk.Frame(main_container, bg=self.colors['warning'], padx=25, pady=18)
        header_card.pack(fill=tk.X, pady=(0, 20))
        tk.Label(header_card, text="📋 Transaction History",
                font=('Segoe UI', 16, 'bold'), bg=self.colors['warning'], fg='white').pack(anchor='w')
        tk.Label(header_card, text="View, filter, and manage all your transactions",
                font=('Segoe UI', 10), bg=self.colors['warning'], fg='#FEF9E7').pack(anchor='w', pady=(5,0))
        
        # Filter section
        filter_card = tk.Frame(main_container, bg=self.colors['card'], padx=20, pady=18)
        filter_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(filter_card, text="🔍 Filter Transactions",
                font=('Segoe UI', 12, 'bold'), bg=self.colors['card'], fg=self.colors['primary']).pack(anchor='w')
        
        filter_controls = tk.Frame(filter_card, bg=self.colors['card'])
        filter_controls.pack(anchor='w', pady=(12, 0))
        
        tk.Label(filter_controls, text="Category:",
                font=('Segoe UI', 10), bg=self.colors['card'], fg=self.colors['dark']).pack(side=tk.LEFT, padx=(0, 10))
        self.filter_category = ttk.Combobox(filter_controls, width=25, font=('Segoe UI', 10))
        self.filter_category.pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(filter_controls, text="🔎 Apply", style='Primary.TButton',
                  command=self.filter_transactions).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(filter_controls, text="✖️ Clear", 
                  command=self.load_transactions).pack(side=tk.LEFT)
        
        # Transactions list card
        list_card = tk.Frame(main_container, bg=self.colors['card'], padx=2, pady=2)
        list_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        list_inner = tk.Frame(list_card, bg='white')
        list_inner.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_inner)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview with modern styling
        self.trans_tree = ttk.Treeview(list_inner, yscrollcommand=scrollbar.set,
                                       columns=('ID', 'Date', 'Type', 'Category', 'Amount', 'Description'),
                                       show='headings', height=12)
        
        # Configure headings with icons
        self.trans_tree.heading('ID', text='#')
        self.trans_tree.heading('Date', text='📅 Date')
        self.trans_tree.heading('Type', text='📊 Type')
        self.trans_tree.heading('Category', text='📁 Category')
        self.trans_tree.heading('Amount', text='💰 Amount')
        self.trans_tree.heading('Description', text='📝 Description')
        
        self.trans_tree.column('ID', width=50, anchor='center')
        self.trans_tree.column('Date', width=110, anchor='center')
        self.trans_tree.column('Type', width=90, anchor='center')
        self.trans_tree.column('Category', width=140)
        self.trans_tree.column('Amount', width=110, anchor='e')
        self.trans_tree.column('Description', width=280)
        
        self.trans_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.trans_tree.yview)
        
        # Action buttons row
        action_frame = tk.Frame(main_container, bg=self.colors['bg'])
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="🗑️ Delete Selected", style='Danger.TButton',
                  command=self.delete_transaction).pack(side=tk.LEFT)
        ttk.Button(action_frame, text="🔄 Refresh List", 
                  command=self.load_transactions).pack(side=tk.LEFT, padx=(10, 0))
    
    def _create_analytics_tab(self):
        """Analytics with charts - Matplotlib"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Analytics")
        
        # Main container
        main_container = ttk.Frame(tab)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header card
        header_card = tk.Frame(main_container, bg='#9B59B6', padx=25, pady=18)
        header_card.pack(fill=tk.X, pady=(0, 20))
        tk.Label(header_card, text="📊 Financial Analytics",
                font=('Segoe UI', 16, 'bold'), bg='#9B59B6', fg='white').pack(anchor='w')
        tk.Label(header_card, text="Visualize your spending patterns and financial statistics",
                font=('Segoe UI', 10), bg='#9B59B6', fg='#E8DAEF').pack(anchor='w', pady=(5,0))
        
        # Controls card
        control_card = tk.Frame(main_container, bg=self.colors['card'], padx=20, pady=18)
        control_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(control_card, text="📈 Chart Controls",
                font=('Segoe UI', 12, 'bold'), bg=self.colors['card'], fg=self.colors['primary']).pack(anchor='w')
        
        controls = tk.Frame(control_card, bg=self.colors['card'])
        controls.pack(anchor='w', pady=(12, 0))
        
        tk.Label(controls, text="Analysis Type:",
                font=('Segoe UI', 10), bg=self.colors['card'], fg=self.colors['dark']).pack(side=tk.LEFT, padx=(0, 10))
        self.chart_type = ttk.Combobox(controls, width=28, state='readonly', font=('Segoe UI', 10))
        self.chart_type['values'] = ['🥧 Category Pie Chart', '📊 Monthly Trend', '📉 Statistics']
        self.chart_type.current(0)
        self.chart_type.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(controls, text="🎨 Generate Charts", style='Primary.TButton',
                  command=self.generate_analytics).pack(side=tk.LEFT)
        
        # Two-column layout for stats and chart
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left: Statistics display
        stats_card = tk.Frame(content_frame, bg=self.colors['card'], padx=20, pady=18)
        stats_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(stats_card, text="📋 Statistics Summary",
                font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['primary']).pack(anchor='w', pady=(0, 10))
        
        self.stats_text = scrolledtext.ScrolledText(stats_card, height=12, wrap=tk.WORD, width=35)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.stats_text.configure(
            bg='#F8F9FA',
            fg=self.colors['dark'],
            relief='flat',
            borderwidth=0,
            font=('Consolas', 10),
            padx=10, pady=10
        )
        
        # Right: Chart area
        chart_card = tk.Frame(content_frame, bg=self.colors['card'], padx=20, pady=18)
        chart_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        tk.Label(chart_card, text="📈 Visualization",
                font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['primary']).pack(anchor='w', pady=(0, 10))
        
        self.analytics_chart_frame = tk.Frame(chart_card, bg=self.colors['card'])
        self.analytics_chart_frame.pack(fill=tk.BOTH, expand=True)
    
    def _create_predictions_tab(self):
        """ML predictions tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🤖 Predictions")
        
        # Main container
        main_container = ttk.Frame(tab)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header card
        header_card = tk.Frame(main_container, bg='#1ABC9C', padx=25, pady=18)
        header_card.pack(fill=tk.X, pady=(0, 20))
        tk.Label(header_card, text="🤖 AI-Powered Predictions",
                font=('Segoe UI', 16, 'bold'), bg='#1ABC9C', fg='white').pack(anchor='w')
        tk.Label(header_card, text="Machine learning predictions based on your spending patterns",
                font=('Segoe UI', 10), bg='#1ABC9C', fg='#D1F2EB').pack(anchor='w', pady=(5,0))
        
        # Controls card
        control_card = tk.Frame(main_container, bg=self.colors['card'], padx=20, pady=18)
        control_card.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(control_card, text="🔮 Prediction Settings",
                font=('Segoe UI', 12, 'bold'), bg=self.colors['card'], fg=self.colors['primary']).pack(anchor='w')
        
        controls = tk.Frame(control_card, bg=self.colors['card'])
        controls.pack(anchor='w', pady=(12, 0))
        
        tk.Label(controls, text="Forecast period:",
                font=('Segoe UI', 10), bg=self.colors['card'], fg=self.colors['dark']).pack(side=tk.LEFT, padx=(0, 10))
        self.predict_days = ttk.Spinbox(controls, from_=1, to=365, width=10, font=('Segoe UI', 11))
        self.predict_days.set(30)
        self.predict_days.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(controls, text="days ahead",
                font=('Segoe UI', 10), bg=self.colors['card'], fg='#7F8C8D').pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(controls, text="🚀 Generate Prediction", style='Primary.TButton',
                  command=self.generate_prediction).pack(side=tk.LEFT)
        
        # Metrics cards row
        metrics_frame = tk.Frame(main_container, bg=self.colors['bg'])
        metrics_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Prediction card
        self.pred_card = tk.Frame(metrics_frame, bg='#3498DB', padx=25, pady=20)
        self.pred_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(self.pred_card, text="📈 Predicted Expense", font=("Segoe UI", 10),
                bg='#3498DB', fg='#D6EAF8').pack(anchor='w')
        self.pred_value_label = tk.Label(self.pred_card, text="$0.00", 
                                         font=("Segoe UI", 28, "bold"), bg='#3498DB', fg='white')
        self.pred_value_label.pack(anchor='w', pady=(8, 0))
        self.pred_period_label = tk.Label(self.pred_card, text="for 30 days",
                                          font=("Segoe UI", 9), bg='#3498DB', fg='#AED6F1')
        self.pred_period_label.pack(anchor='w', pady=(5, 0))
        
        # Daily rate card
        self.rate_card = tk.Frame(metrics_frame, bg='#27AE60', padx=25, pady=20)
        self.rate_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)
        tk.Label(self.rate_card, text="💵 Daily Rate", font=("Segoe UI", 10),
                bg='#27AE60', fg='#D5F5E3').pack(anchor='w')
        self.rate_value_label = tk.Label(self.rate_card, text="$0.00/day",
                                         font=("Segoe UI", 28, "bold"), bg='#27AE60', fg='white')
        self.rate_value_label.pack(anchor='w', pady=(8, 0))
        self.rate_trend_label = tk.Label(self.rate_card, text="spending trend",
                                         font=("Segoe UI", 9), bg='#27AE60', fg='#A9DFBF')
        self.rate_trend_label.pack(anchor='w', pady=(5, 0))
        
        # Confidence card
        self.conf_card = tk.Frame(metrics_frame, bg='#9B59B6', padx=25, pady=20)
        self.conf_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))
        tk.Label(self.conf_card, text="🎯 Model Confidence", font=("Segoe UI", 10),
                bg='#9B59B6', fg='#E8DAEF').pack(anchor='w')
        self.conf_value_label = tk.Label(self.conf_card, text="0%",
                                         font=("Segoe UI", 28, "bold"), bg='#9B59B6', fg='white')
        self.conf_value_label.pack(anchor='w', pady=(8, 0))
        self.conf_desc_label = tk.Label(self.conf_card, text="R² score",
                                        font=("Segoe UI", 9), bg='#9B59B6', fg='#D7BDE2')
        self.conf_desc_label.pack(anchor='w', pady=(5, 0))
        
        # Interpretation panel
        interp_card = tk.Frame(main_container, bg=self.colors['card'], padx=25, pady=20)
        interp_card.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(interp_card, text="🔍 Analysis & Interpretation",
                font=('Segoe UI', 12, 'bold'), bg=self.colors['card'], fg=self.colors['primary']).pack(anchor='w', pady=(0, 12))
        
        self.prediction_text = tk.Text(interp_card, height=8, wrap=tk.WORD,
                                       font=("Segoe UI", 11), relief='flat', padx=15, pady=15)
        self.prediction_text.pack(fill=tk.BOTH, expand=True)
        self.prediction_text.configure(bg='#F8F9FA', fg=self.colors['dark'])
        
        # Configure text tags for styling
        self.prediction_text.tag_configure('header', font=("Segoe UI", 12, "bold"), 
                                           foreground=self.colors['primary'])
        self.prediction_text.tag_configure('positive', foreground='#27AE60')
        self.prediction_text.tag_configure('negative', foreground='#E74C3C')
        self.prediction_text.tag_configure('neutral', foreground=self.colors['dark'])
    
    def refresh_dashboard(self):
        """Refresh dashboard data - Control Flow"""
        stats = self.db.get_summary_stats()
        
        # Update values (text is white on colored cards now)
        self.summary_labels['Total Income'].config(
            text=f"${stats['total_income']:.2f}")
        self.summary_labels['Total Expenses'].config(
            text=f"${stats['total_expenses']:.2f}")
        
        # Net balance with status
        net = stats['net_balance']
        if net > 0:
            status = '↑ Positive'
        elif net < 0:
            status = '↓ Negative'
        else:
            status = '→ Zero'
        
        self.summary_labels['Net Balance'].config(
            text=f"${net:.2f}")
        self.summary_labels['Transaction Count'].config(
            text=str(stats['transaction_count']))
        
        # Update category chart
        self._update_dashboard_chart()
        
        # Update status
        self.status_bar.config(text=f"Dashboard refreshed at {datetime.now().strftime('%H:%M:%S')}")
    
    def _update_dashboard_chart(self):
        """Update dashboard pie chart"""
        for widget in self.dashboard_chart_frame.winfo_children():
            widget.destroy()
        
        category_data = self.db.get_category_summary()
        
        if not category_data:
            no_data_frame = tk.Frame(self.dashboard_chart_frame, bg=self.colors['card'])
            no_data_frame.pack(expand=True)
            tk.Label(no_data_frame, text="📊", font=('Segoe UI', 40),
                    bg=self.colors['card'], fg='#BDC3C7').pack(pady=(20, 10))
            tk.Label(no_data_frame, text="No expense data available",
                    font=('Segoe UI', 12), bg=self.colors['card'], fg='#7F8C8D').pack()
            tk.Label(no_data_frame, text="Add some transactions to see the breakdown",
                    font=('Segoe UI', 10), bg=self.colors['card'], fg='#BDC3C7').pack(pady=(5, 20))
            return
        
        # Matplotlib chart with custom colors
        fig = Figure(figsize=(6, 4), facecolor=self.colors['card'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.colors['card'])
        
        categories = [c[0] for c in category_data]
        amounts = [c[1] for c in category_data]
        
        # Custom color palette
        colors = ['#3498DB', '#E74C3C', '#27AE60', '#F39C12', '#9B59B6', '#1ABC9C', '#E67E22', '#34495E']
        
        result = ax.pie(amounts, labels=categories, autopct='%1.1f%%', 
                        startangle=90, colors=colors[:len(categories)],
                        textprops={'fontsize': 9})
        # autopct returns 3 values: wedges, texts, autotexts
        if len(result) == 3:
            autotexts = result[2]
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        ax.set_title('', pad=10)
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.dashboard_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def add_transaction(self):
        """Add new transaction - User Input, Casting"""
        try:
            # Get and validate input - Casting
            amount = float(self.amount_entry.get().strip())
            category = self.category_entry.get().strip()
            description = self.desc_entry.get().strip()
            date = self.date_entry.get().strip()
            trans_type = self.trans_type.get()
            
            # Input validation - Control Flow
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
            
            if not category:
                messagebox.showerror("Error", "Category is required")
                return
            
            # Create transaction object - Classes
            if trans_type == "Income":
                transaction = Income(0, amount, category, description, date, source=category)
            else:
                transaction = Expense(0, amount, category, description, date, payment_method="Card")
            
            # Save to database
            self.db.add_transaction(transaction)
            
            # Success message with f-string
            messagebox.showinfo("Success", f"{trans_type} of ${amount:.2f} added successfully!")
            
            self.clear_form()
            self.refresh_dashboard()
            self.load_transactions()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number.")
    
    def clear_form(self):
        """Clear input form"""
        self.amount_entry.delete(0, tk.END)
        self.category_entry.set('')
        self.desc_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
    
    def load_transactions(self):
        """Load all transactions into treeview"""
        # Clear existing
        for item in self.trans_tree.get_children():
            self.trans_tree.delete(item)
        
        # Load from database
        transactions = self.db.get_all_transactions()
        
        # Populate treeview - Loops
        for trans in transactions:
            # F-string formatting with placeholders
            amount_str = f"${trans.amount:.2f}"
            self.trans_tree.insert('', 'end', values=(
                trans.transaction_id,
                trans.date,
                trans.__class__.__name__,
                trans.category,
                amount_str,
                trans.description
            ))
        
        # Update filter categories
        categories = list(self.db.get_categories())
        self.filter_category['values'] = ['All'] + categories
    
    def filter_transactions(self):
        """Filter transactions by category - Lambda"""
        category = self.filter_category.get()
        
        if not category or category == 'All':
            self.load_transactions()
            return
        
        # Clear treeview
        for item in self.trans_tree.get_children():
            self.trans_tree.delete(item)
        
        # Use custom iterator with lambda filter
        all_trans = self.db.get_all_transactions()
        filtered = TransactionIterator(
            all_trans, 
            filter_func=lambda t: t.category.lower() == category.lower()
        )
        
        # Display filtered results
        for trans in filtered:
            amount_str = f"${trans.amount:.2f}"
            self.trans_tree.insert('', 'end', values=(
                trans.transaction_id,
                trans.date,
                trans.__class__.__name__,
                trans.category,
                amount_str,
                trans.description
            ))
    
    def delete_transaction(self):
        """Delete selected transaction"""
        selected = self.trans_tree.selection()
        
        if not selected:
            messagebox.showwarning("Warning", "Please select a transaction to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected transaction?"):
            item = self.trans_tree.item(selected[0])
            trans_id = int(item['values'][0])
            self.db.delete_transaction(trans_id)
            self.load_transactions()
            self.refresh_dashboard()
    
    def generate_analytics(self):
        """Generate analytics charts - Matplotlib, NumPy, Statistics"""
        chart_type = self.chart_type.get()
        transactions = self.db.get_all_transactions()
        
        if not transactions:
            messagebox.showinfo("Info", "No data available for analytics")
            return
        
        # Clear previous chart
        for widget in self.analytics_chart_frame.winfo_children():
            widget.destroy()
        
        # Get expense amounts for statistics
        expense_amounts = [t.amount for t in transactions if isinstance(t, Expense)]
        
        basic_stats = None
        if expense_amounts:
            # Calculate statistics
            basic_stats = self.analyzer.calculate_statistics(expense_amounts)
            numpy_stats = self.analyzer.numpy_operations(expense_amounts)
            scipy_stats = self.analyzer.scipy_analysis(expense_amounts)
            
            # Display statistics with placeholders
            stats_text = f"""
EXPENSE STATISTICS
==================
Mean (Average): ${basic_stats['mean']:.2f}
Median: ${basic_stats['median']:.2f}
Mode: ${basic_stats['mode']:.2f}
Standard Deviation: ${basic_stats['std_dev']:.2f}
Min: ${basic_stats['min']:.2f}
Max: ${basic_stats['max']:.2f}

NUMPY ANALYSIS
==============
Sum: ${numpy_stats['sum']:.2f}
25th Percentile: ${numpy_stats['percentile_25']:.2f}
75th Percentile: ${numpy_stats['percentile_75']:.2f}

SCIPY ANALYSIS
==============
Skewness: {scipy_stats['skewness']:.4f}
Kurtosis: {scipy_stats['kurtosis']:.4f}
"""
            self.stats_text.delete('1.0', tk.END)
            self.stats_text.insert('1.0', stats_text)
        
        # Generate selected chart
        fig = Figure(figsize=(8, 5), facecolor=self.colors['card'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.colors['card'])
        
        if 'Pie' in chart_type:
            percentages = self.analyzer.category_percentages(transactions)
            if percentages:
                colors = ['#3498DB', '#E74C3C', '#27AE60', '#F39C12', '#9B59B6', '#1ABC9C', '#E67E22', '#34495E']
                result = ax.pie(list(percentages.values()), labels=list(percentages.keys()), 
                      autopct='%1.1f%%', startangle=90, colors=colors[:len(percentages)])
                if len(result) == 3:
                    for autotext in result[2]:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                ax.set_title('Spending Distribution by Category', fontsize=12, fontweight='bold')
        
        elif 'Trend' in chart_type:
            months, income_vals, expense_vals = self.analyzer.monthly_trend(transactions)
            if months:
                x = np.arange(len(months))
                width = 0.35
                ax.bar(x - width/2, income_vals, width, label='Income', color='#27AE60')
                ax.bar(x + width/2, expense_vals, width, label='Expenses', color='#E74C3C')
                ax.set_xlabel('Month')
                ax.set_ylabel('Amount ($)')
                ax.set_title('Monthly Income vs Expenses', fontsize=12, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(months, rotation=45)
                ax.legend()
                fig.tight_layout()
        
        elif 'Statistics' in chart_type:
            if expense_amounts and basic_stats:
                ax.hist(expense_amounts, bins=10, edgecolor='white', alpha=0.8, color='#3498DB')
                ax.axvline(basic_stats['mean'], color='#E74C3C', linestyle='--', linewidth=2,
                          label=f"Mean: ${basic_stats['mean']:.2f}")
                ax.axvline(basic_stats['median'], color='#27AE60', linestyle='--', linewidth=2,
                          label=f"Median: ${basic_stats['median']:.2f}")
                ax.set_xlabel('Expense Amount ($)')
                ax.set_ylabel('Frequency')
                ax.set_title('Expense Distribution', fontsize=12, fontweight='bold')
                ax.legend()
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, self.analytics_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def generate_prediction(self):
        """Generate ML prediction - Machine Learning, Linear Regression"""
        transactions = self.db.get_all_transactions()
        
        if len(transactions) < 2:
            messagebox.showinfo("Info", "Need at least 2 transactions for prediction")
            return
        
        try:
            days = int(self.predict_days.get())
            prediction = self.analyzer.predict_spending(transactions, days)
            
            # Update metric cards
            self.pred_value_label.config(text=f"${prediction['prediction']:.2f}")
            self.pred_period_label.config(text=f"for {days} days")
            
            # Daily rate with trend indicator
            rate = prediction['daily_rate']
            if rate > 0:
                self.rate_value_label.config(text=f"+${rate:.2f}/day")
                self.rate_trend_label.config(text="↗ increasing trend")
                self.rate_card.config(bg='#E74C3C')  # Red for increasing expense
                for widget in self.rate_card.winfo_children():
                    widget.configure(bg='#E74C3C')  # type: ignore
            elif rate < 0:
                self.rate_value_label.config(text=f"-${abs(rate):.2f}/day")
                self.rate_trend_label.config(text="↘ decreasing trend")
                self.rate_card.config(bg='#27AE60')  # Green for decreasing
                for widget in self.rate_card.winfo_children():
                    widget.configure(bg='#27AE60')  # type: ignore
            else:
                self.rate_value_label.config(text=f"${rate:.2f}/day")
                self.rate_trend_label.config(text="→ stable trend")
                self.rate_card.config(bg='#F39C12')  # Orange for stable
                for widget in self.rate_card.winfo_children():
                    widget.configure(bg='#F39C12')  # type: ignore
            
            # Confidence with color coding
            r_squared = prediction['r_squared']
            confidence_pct = int(r_squared * 100)
            self.conf_value_label.config(text=f"{confidence_pct}%")
            
            if r_squared > 0.8:
                self.conf_card.config(bg='#27AE60')
                self.conf_desc_label.config(text="High confidence")
                conf_level = "HIGH"
            elif r_squared > 0.5:
                self.conf_card.config(bg='#F39C12')
                self.conf_desc_label.config(text="Moderate confidence")
                conf_level = "MODERATE"
            else:
                self.conf_card.config(bg='#E74C3C')
                self.conf_desc_label.config(text="Low confidence")
                conf_level = "LOW"
            
            for widget in self.conf_card.winfo_children():
                widget.configure(bg=self.conf_card.cget('bg'))  # type: ignore
            
            # Update interpretation text
            self.prediction_text.delete('1.0', tk.END)
            
            self.prediction_text.insert(tk.END, "PREDICTION SUMMARY\n", 'header')
            self.prediction_text.insert(tk.END, "─" * 40 + "\n\n")
            
            self.prediction_text.insert(tk.END, f"Based on your spending history, the ML model predicts you will spend approximately ")
            self.prediction_text.insert(tk.END, f"${prediction['prediction']:.2f}", 'negative' if prediction['prediction'] > 0 else 'positive')
            self.prediction_text.insert(tk.END, f" over the next {days} days.\n\n")
            
            self.prediction_text.insert(tk.END, "TREND ANALYSIS\n", 'header')
            self.prediction_text.insert(tk.END, "─" * 40 + "\n\n")
            
            if rate > 0:
                self.prediction_text.insert(tk.END, "⚠️ Your spending is ", 'neutral')
                self.prediction_text.insert(tk.END, f"INCREASING by ${rate:.2f}/day", 'negative')
                self.prediction_text.insert(tk.END, ".\nConsider reviewing your budget to control expenses.\n\n", 'neutral')
            elif rate < 0:
                self.prediction_text.insert(tk.END, "✅ Great news! Your spending is ", 'neutral')
                self.prediction_text.insert(tk.END, f"DECREASING by ${abs(rate):.2f}/day", 'positive')
                self.prediction_text.insert(tk.END, ".\nYou're on track with your savings goals!\n\n", 'neutral')
            else:
                self.prediction_text.insert(tk.END, "➡️ Your spending is relatively ", 'neutral')
                self.prediction_text.insert(tk.END, "STABLE", 'neutral')
                self.prediction_text.insert(tk.END, ".\nNo significant changes detected in your spending pattern.\n\n", 'neutral')
            
            self.prediction_text.insert(tk.END, "MODEL CONFIDENCE\n", 'header')
            self.prediction_text.insert(tk.END, "─" * 40 + "\n\n")
            
            if conf_level == "HIGH":
                self.prediction_text.insert(tk.END, f"🎯 {conf_level} confidence (R² = {r_squared:.3f})\n", 'positive')
                self.prediction_text.insert(tk.END, "The model found a strong linear pattern in your spending data. These predictions are reliable.\n")
            elif conf_level == "MODERATE":
                self.prediction_text.insert(tk.END, f"🎯 {conf_level} confidence (R² = {r_squared:.3f})\n", 'neutral')
                self.prediction_text.insert(tk.END, "The model found some patterns, but your spending has variability. Use predictions as guidance.\n")
            else:
                self.prediction_text.insert(tk.END, f"🎯 {conf_level} confidence (R² = {r_squared:.3f})\n", 'negative')
                self.prediction_text.insert(tk.END, "Your spending pattern is irregular. Consider adding more transaction data for better predictions.\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Prediction failed: {str(e)}")
    
    def add_sample_data(self):
        """Add sample transactions for testing"""
        from datetime import timedelta
        
        sample_data = [
            ('Expense', 45.50, 'Food', 'Grocery shopping', 0),
            ('Expense', 12.99, 'Transportation', 'Gas', 1),
            ('Income', 2500.00, 'Salary', 'Monthly paycheck', 2),
            ('Expense', 89.99, 'Entertainment', 'Concert tickets', 3),
            ('Expense', 150.00, 'Utilities', 'Electric bill', 5),
            ('Expense', 32.50, 'Food', 'Restaurant', 7),
            ('Expense', 25.00, 'Transportation', 'Parking', 10),
            ('Income', 500.00, 'Investment', 'Stock dividend', 12),
            ('Expense', 75.00, 'Entertainment', 'Movies', 15),
            ('Expense', 60.00, 'Food', 'Groceries', 18),
        ]
        
        base_date = datetime.now()
        
        for ttype, amount, category, desc, days_ago in sample_data:
            date = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            if ttype == 'Income':
                trans = Income(0, amount, category, desc, date, source=category)
            else:
                trans = Expense(0, amount, category, desc, date, payment_method="Card")
            
            self.db.add_transaction(trans)
        
        messagebox.showinfo("Success", "Sample data added successfully!")
        self.refresh_dashboard()
        self.load_transactions()
    
    def clear_all_data(self):
        """Clear all data from database"""
        if messagebox.askyesno("Confirm", "Delete ALL transactions? This cannot be undone!"):
            self.db.clear_all()
            self.refresh_dashboard()
            self.load_transactions()
            messagebox.showinfo("Success", "All data cleared")
    
    def on_closing(self):
        """Clean up before closing"""
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = FinanceTrackerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
