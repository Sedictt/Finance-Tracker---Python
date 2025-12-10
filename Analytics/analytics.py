import customtkinter as ctk
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Database Configuration (matches the file in your root folder)
DB_FILE = "finance_ctk.db"

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 

        # --- 1. Header Section ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Financial Analytics", 
                                      font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(side="left")

        # View Switcher
        self.view_type = ctk.StringVar(value="Monthly Overview")
        self.view_switcher = ctk.CTkSegmentedButton(self.header_frame, 
                                                    values=["Monthly Overview", "Category Breakdown"],
                                                    variable=self.view_type,
                                                    command=self.refresh_charts)
        self.view_switcher.pack(side="right")

        # --- 2. Content Area (Charts) ---
        self.chart_frame = ctk.CTkFrame(self, fg_color="#1E1E1E") 
        self.chart_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Internal container for the canvas
        self.canvas_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Initial Load
        self.refresh_charts(None)

    def fetch_data(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            # We use a query to join transactions with category names
            query = """
                SELECT t.date, t.amount, c.name as category 
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
            """
            df = pd.read_sql_query(query, conn)
            conn.close()

            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df['month_year'] = df['date'].dt.to_period('M')
                df['type'] = df['amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
                df['abs_amount'] = df['amount'].abs()
            return df
        except Exception as e:
            print(f"Error fetching analytics data: {e}")
            return pd.DataFrame()

    def refresh_charts(self, value):
        # Clear previous charts
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        df = self.fetch_data()

        if df.empty:
            ctk.CTkLabel(self.canvas_frame, text="No transaction data available yet.").pack(expand=True)
            return

        # Setup Plot
        plt.style.use('dark_background')
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        fig.patch.set_facecolor('#1E1E1E') 
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1E1E1E')

        if self.view_type.get() == "Monthly Overview":
            self._draw_monthly_bar(ax, df)
        else:
            self._draw_category_bar(ax, df)

        # Render to Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_monthly_bar(self, ax, df):
        monthly = df.groupby(['month_year', 'type'])['abs_amount'].sum().unstack(fill_value=0)
        months = monthly.index.astype(str)
        x = range(len(months))
        width = 0.35

        income = monthly.get('Income', [0]*len(months))
        expense = monthly.get('Expense', [0]*len(months))

        ax.bar([i - width/2 for i in x], income, width, label='Income', color='#2ecc71')
        ax.bar([i + width/2 for i in x], expense, width, label='Expenses', color='#e74c3c')

        ax.set_title('Income vs Expenses', color='white', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45)
        ax.legend(facecolor='#1E1E1E')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    def _draw_category_bar(self, ax, df):
        expenses = df[df['amount'] < 0]
        if expenses.empty:
            return
        
        cat_group = expenses.groupby('category')['abs_amount'].sum().sort_values().tail(7)
        ax.barh(cat_group.index, cat_group.values, color='#3498db')
        ax.set_title('Top Expenses by Category', color='white', pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)