import customtkinter as ctk
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Database Configuration (matches the file in your root folder)
DB_FILE = "finance_ctk.db"

# -------------------------
# Modern Color Palette
# -------------------------
COLOR_BG_CARD = "#2b2b2b"
COLOR_PRIMARY = "#2B2D42"
COLOR_SECONDARY = "#8D99AE"
COLOR_ACCENT = "#D90429"
COLOR_TEXT_PRIMARY = "#FFFFFF"

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Main chart area expands

        # --- Base Container ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(3, weight=1) 

        # --- 1. Header Section ---
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Deep Dive Analytics", 
                                      font=ctk.CTkFont(family="Roboto", size=26, weight="bold"))
        self.title_label.pack(side="left")
        
        self.subtitle = ctk.CTkLabel(self.header_frame, text=" |  Trends, Trajectories & Ratios", 
                                   text_color=COLOR_SECONDARY, font=ctk.CTkFont(family="Roboto", size=14))
        self.subtitle.pack(side="left", padx=10, pady=(8,0))
        
        # Refresh Button
        self.btn_refresh = ctk.CTkButton(self.header_frame, text="↻ Refresh", 
                                       command=lambda: self.refresh_charts(None),
                                       font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
                                       fg_color=COLOR_BG_CARD, border_width=1, border_color=COLOR_SECONDARY, 
                                       hover_color="#3E4059", height=32, width=80)
        self.btn_refresh.pack(side="right")

        # --- 2. Advanced Metrics (KPIs distinct from Dashboard) ---
        self.stats_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        self.stats_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        # We focus on RATES/RATIOS and AVERAGES here, not just totals
        self.kpi_savings_rate = self.create_kpi_card(self.stats_frame, "Savings Rate (All Time)", "--%", 0)
        self.kpi_daily_avg = self.create_kpi_card(self.stats_frame, "Avg Daily Spend", "--", 1)
        self.kpi_volatility = self.create_kpi_card(self.stats_frame, "Monthly Variability", "--", 2)
        self.kpi_largest_tx = self.create_kpi_card(self.stats_frame, "Largest Single Expense", "--", 3)

        # --- 3. Comparison Controls ---
        self.controls_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(self.controls_frame, text="Chart Focus:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0,10))
        self.chart_view_var = ctk.StringVar(value="Wealth Trajectory")
        self.chart_switcher = ctk.CTkSegmentedButton(self.controls_frame, 
                                                    values=["Wealth Trajectory", "Categorical Trends"],
                                                    variable=self.chart_view_var,
                                                    command=self.refresh_charts)
        self.chart_switcher.pack(side="left")


        # --- 4. Main Analytic Chart Area ---
        self.chart_frame = ctk.CTkFrame(self.main_container, fg_color=COLOR_BG_CARD, corner_radius=15)
        self.chart_frame.grid(row=3, column=0, sticky="nsew")
        
        self.canvas_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Initial Load
        self.refresh_charts(None)

    def create_kpi_card(self, parent, title, initial_val, col_idx):
        frame = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=12)
        frame.grid(row=0, column=col_idx, padx=5, sticky="ew")
        
        lbl_title = ctk.CTkLabel(frame, text=title, text_color="gray70", font=ctk.CTkFont(size=11))
        lbl_title.pack(padx=15, pady=(15, 0), anchor="w")
        
        lbl_val = ctk.CTkLabel(frame, text=initial_val, text_color="white", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_val.pack(padx=15, pady=(5, 15), anchor="w")
        
        return lbl_val

    def fetch_data(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            query = """
                SELECT t.date, t.amount, c.name as category 
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                ORDER BY t.date ASC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()

            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df['month_year'] = df['date'].dt.to_period('M')
                # Separate Income and Expense
                df['income'] = df['amount'].apply(lambda x: x if x > 0 else 0)
                df['expense'] = df['amount'].apply(lambda x: abs(x) if x < 0 else 0)
            return df
        except Exception as e:
            print(f"Error fetching analytics data: {e}")
            return pd.DataFrame()

    def refresh_charts(self, value):
        for widget in self.canvas_frame.winfo_children(): widget.destroy()

        df = self.fetch_data()
        
        if df.empty:
            ctk.CTkLabel(self.canvas_frame, text="Need more data to generate deep insights.", font=ctk.CTkFont(size=16)).pack(expand=True)
            self.kpi_savings_rate.configure(text="--")
            return

        # --- Calculate Advanced Metrics ---
        total_income = df['income'].sum()
        total_expense = df['expense'].sum()
        
        # 1. Savings Rate
        if total_income > 0:
            savings_rate = ((total_income - total_expense) / total_income) * 100
            self.kpi_savings_rate.configure(text=f"{savings_rate:.1f}%")
        else:
            self.kpi_savings_rate.configure(text="0.0%")
            
        # 2. Daily Average Spend (Active Days span)
        days_span = (df['date'].max() - df['date'].min()).days + 1
        avg_daily = total_expense / max(1, days_span)
        self.kpi_daily_avg.configure(text=f"${avg_daily:,.2f}")
        
        # 3. Monthly Volatility (Std Dev of Monthly Expense)
        monthly_exp = df.groupby('month_year')['expense'].sum()
        if len(monthly_exp) > 1:
            volatility = monthly_exp.std()
            self.kpi_volatility.configure(text=f"±${volatility:,.0f}")
        else:
            self.kpi_volatility.configure(text="Stable")

        # 4. Largest Single Expense
        max_tx = df[df['amount'] < 0]['amount'].min() # min because it's negative
        if pd.isna(max_tx):
            self.kpi_largest_tx.configure(text="$0.00")
        else:
            self.kpi_largest_tx.configure(text=f"${abs(max_tx):,.2f}")
            
        # --- Draw Selected Chart ---
        fig, ax = self._get_figure()
        
        if self.chart_view_var.get() == "Wealth Trajectory":
            self._plot_wealth_trajectory(ax, df)
        else:
            self._plot_category_trends(ax, df)
            
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _get_figure(self):
        plt.style.use('dark_background')
        fig = plt.Figure(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor(COLOR_BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLOR_BG_CARD)
        return fig, ax

    def _plot_wealth_trajectory(self, ax, df):
        # Calculate cumulative sum of all transactions (running balance)
        df['cumulative_balance'] = df['amount'].cumsum()
        
        # Smooth line
        ax.plot(df['date'], df['cumulative_balance'], color='#4CC9F0', linewidth=2, label='Net Wealth')
        
        # Fill area under curve
        ax.fill_between(df['date'], df['cumulative_balance'], alpha=0.1, color='#4CC9F0')
        
        ax.set_title("Wealth Accumulation Trajectory", fontsize=14, color='white', pad=20)
        ax.set_ylabel("Net Balance ($)", fontsize=10, color='gray')
        
        # Style
        ax.grid(True, linestyle='--', alpha=0.15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#888')
        ax.spines['left'].set_color('#888')
        ax.tick_params(colors='gray')
        
        # Add a trend line (Polyfit)
        # Convert dates to numbers for regression
        import matplotlib.dates as mdates
        if len(df) > 1:
            x_nums = mdates.date2num(df['date'])
            z = np.polyfit(x_nums, df['cumulative_balance'], 1)
            p = np.poly1d(z)
            ax.plot(df['date'], p(x_nums), "r--", alpha=0.5, linewidth=1, label="Trend")
            ax.legend(frameon=False, labelcolor='white')

    def _plot_category_trends(self, ax, df):
        # Top 5 Categories over time (Monthly)
        df_exp = df[df['amount'] < 0].copy()
        if df_exp.empty: return
        
        # Get top 4 categories by total volume
        top_cats = df_exp.groupby('category')['expense'].sum().nlargest(4).index.tolist()
        
        # Filter data to these categories
        df_top = df_exp[df_exp['category'].isin(top_cats)]
        
        # Pivot: Month on X, Category on Y (stacks)
        pivot = df_top.groupby(['month_year', 'category'])['expense'].sum().unstack(fill_value=0)
        
        if pivot.empty: return

        # Plot
        pivot.plot(kind='area', stacked=True, ax=ax, alpha=0.7, colormap='viridis')
        
        ax.set_title("Top Spending Categories Trends (Monthly)", fontsize=14, color='white', pad=20)
        ax.set_xlabel("")
        ax.legend(frameon=False, labelcolor='white', loc='upper left')
        
        # Style
        ax.grid(True, linestyle='--', alpha=0.15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#888')
        ax.spines['left'].set_color('#888')
        ax.tick_params(colors='gray')