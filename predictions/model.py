import customtkinter as ctk
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import datetime
from tkinter import filedialog, messagebox

class AnalysisSettingsModal(ctk.CTkToplevel):
    def __init__(self, parent, current_settings, on_run_callback):
        super().__init__(parent)
        self.title("Analysis Settings")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self.on_run_callback = on_run_callback
        self.settings = current_settings
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        self.label = ctk.CTkLabel(self, text="Configuration", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Date Range
        self.date_frame = ctk.CTkFrame(self)
        self.date_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.date_label = ctk.CTkLabel(self.date_frame, text="Time Range:", font=ctk.CTkFont(weight="bold"))
        self.date_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.date_var = ctk.StringVar(value=self.settings.get("date_range", "Last 30 Days"))
        self.date_menu = ctk.CTkOptionMenu(self.date_frame, variable=self.date_var,
                                          values=["Last 30 Days", "Last 60 Days", "Last 90 Days"])
        self.date_menu.pack(fill="x", padx=15, pady=(0, 15))
        
        # Graph Options
        self.opts_frame = ctk.CTkFrame(self)
        self.opts_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.opts_label = ctk.CTkLabel(self.opts_frame, text="Graph Visibility:", font=ctk.CTkFont(weight="bold"))
        self.opts_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.hist_var = ctk.BooleanVar(value=self.settings.get("show_history", True))
        ctk.CTkCheckBox(self.opts_frame, text="Show History", variable=self.hist_var).pack(anchor="w", padx=15, pady=2)
        
        self.trend_var = ctk.BooleanVar(value=self.settings.get("show_trend", True))
        ctk.CTkCheckBox(self.opts_frame, text="Show Trend", variable=self.trend_var).pack(anchor="w", padx=15, pady=2)
        
        self.conf_var = ctk.BooleanVar(value=self.settings.get("show_conf", False))
        ctk.CTkCheckBox(self.opts_frame, text="Show Confidence Interval", variable=self.conf_var).pack(anchor="w", padx=15, pady=2)
        
        self.forecast_var = ctk.BooleanVar(value=self.settings.get("show_forecast", True))
        ctk.CTkCheckBox(self.opts_frame, text="Show Forecast", variable=self.forecast_var).pack(anchor="w", padx=15, pady=(2, 15))
        
        # Actions
        self.run_btn = ctk.CTkButton(self, text="Run Analysis & Apply", command=self.apply_and_run,
                                   font=ctk.CTkFont(size=16, weight="bold"), height=40,
                                   fg_color="#1f6aa5", hover_color="#144870")
        self.run_btn.grid(row=3, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.close_btn = ctk.CTkButton(self, text="Cancel", command=self.destroy,
                                     fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.close_btn.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        
    def apply_and_run(self):
        new_settings = {
            "date_range": self.date_var.get(),
            "show_history": self.hist_var.get(),
            "show_trend": self.trend_var.get(),
            "show_conf": self.conf_var.get(),
            "show_forecast": self.forecast_var.get()
        }
        self.on_run_callback(new_settings)
        self.destroy()

class PredictionsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # State
        self.settings = {
            "date_range": "Last 30 Days",
            "show_history": True,
            "show_trend": True,
            "show_conf": False,
            "show_forecast": True
        }
        self.current_df = None
        self.latest_model = None
        self.latest_future_X = None
        self.latest_future_y = None
        self.latest_std_dev = 0
        self.is_sidebar_open = True
        
        # Layout
        self.grid_columnconfigure(0, weight=1) # Graph area
        self.grid_columnconfigure(1, weight=0) # Sidebar (fixed/collapsible)
        self.grid_rowconfigure(1, weight=1)    # Content area
        
        # --- Top Bar ---
        self.top_bar = ctk.CTkFrame(self, height=60, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 0))
        
        self.title_lbl = ctk.CTkLabel(self.top_bar, text="Financial Predictions", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_lbl.pack(side="left", pady=10)
        
        self.subtitle_lbl = ctk.CTkLabel(self.top_bar, text=" |  AI-powered Spending Analysis", 
                                       font=ctk.CTkFont(size=14), text_color="gray60")
        self.subtitle_lbl.pack(side="left", pady=10, padx=10)
        
        # Top Bar Actions
        self.settings_btn = ctk.CTkButton(self.top_bar, text="⚙️ Settings", width=100, 
                                        command=self.open_settings, fg_color="#2B2B2B", border_width=1, border_color="gray50")
        self.settings_btn.pack(side="right", padx=10)
        
        self.toggle_side_btn = ctk.CTkButton(self.top_bar, text="Show Report ◂", width=100,
                                           command=self.toggle_sidebar, fg_color="#2B2B2B", border_width=1, border_color="gray50")
        self.toggle_side_btn.pack(side="right")

        # --- Main Graph Area ---
        self.graph_frame = ctk.CTkFrame(self, corner_radius=15)
        self.graph_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        self.empty_graph_label = ctk.CTkLabel(self.graph_frame, text="Open Settings to Run Analysis",
                                            font=ctk.CTkFont(size=16), text_color="gray50")
        self.empty_graph_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # --- Sidebar (Report Panel) ---
        self.sidebar = ctk.CTkScrollableFrame(self, width=300, corner_radius=0, fg_color=("gray90", "gray15"))
        self.sidebar.grid(row=1, column=1, sticky="nsew", padx=(0, 0), pady=0)
        
        self.setup_sidebar()

    def setup_sidebar(self):
        # Sidebar Content
        self.report_title = ctk.CTkLabel(self.sidebar, text="Analysis Report", font=ctk.CTkFont(size=18, weight="bold"))
        self.report_title.pack(pady=(20, 10), padx=20, anchor="w")
        
        # Forecast Card
        self.forecast_container = ctk.CTkFrame(self.sidebar, fg_color=("white", "gray20"), corner_radius=10, border_width=2, border_color="#3B8ED0")
        self.forecast_container.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(self.forecast_container, text="PROJECTED 7-DAY SPEND", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray70").pack(pady=(10, 2))
        self.forecast_amount_label = ctk.CTkLabel(self.forecast_container, text="--", font=ctk.CTkFont(size=28, weight="bold"), text_color="#3B8ED0")
        self.forecast_amount_label.pack(pady=(0, 2))
        self.forecast_trend_label = ctk.CTkLabel(self.forecast_container, text="Run analysis...", font=ctk.CTkFont(size=12, weight="bold"))
        self.forecast_trend_label.pack(pady=(0, 10))
        
        # Metrics
        ctk.CTkLabel(self.sidebar, text="Key Metrics", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5), padx=20, anchor="w")
        
        self.stat_vars = {
            "Total": ctk.StringVar(value="--"),
            "Mean": ctk.StringVar(value="--"),
            "Median": ctk.StringVar(value="--"),
            "Mode": ctk.StringVar(value="--"),
            "Std Dev": ctk.StringVar(value="--")
        }
        
        self.create_stat_row("Total Spending", self.stat_vars["Total"])
        self.create_stat_row("Avg. Daily", self.stat_vars["Mean"])
        self.create_stat_row("Typical (Median)", self.stat_vars["Median"])
        self.create_stat_row("Most Frequent", self.stat_vars["Mode"])
        self.create_stat_row("Volatility", self.stat_vars["Std Dev"])
        
        # Insights
        ctk.CTkLabel(self.sidebar, text="AI Insights", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")
        self.insights_text = ctk.CTkTextbox(self.sidebar, height=150, fg_color=("white", "gray20"), wrap="word", font=ctk.CTkFont(size=12))
        self.insights_text.pack(fill="x", padx=15, pady=(0, 10))
        self.insights_text.insert("0.0", "No analysis data available.")
        self.insights_text.configure(state="disabled")
        
        # Export
        self.export_btn = ctk.CTkButton(self.sidebar, text="Export CSV", command=self.export_data,
                                        fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.export_btn.pack(fill="x", padx=15, pady=(20, 20))

    def create_stat_row(self, title, variable):
        frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame, text=title, text_color="gray70", font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkLabel(frame, textvariable=variable, font=ctk.CTkFont(size=12, weight="bold")).pack(side="right")

    def open_settings(self):
        AnalysisSettingsModal(self.winfo_toplevel(), self.settings, self.handle_analysis_run)

    def toggle_sidebar(self):
        if self.is_sidebar_open:
            self.sidebar.grid_remove()
            self.toggle_side_btn.configure(text="Show Report ◂")
            self.is_sidebar_open = False
        else:
            self.sidebar.grid()
            self.toggle_side_btn.configure(text="Hide Report ▸")
            self.is_sidebar_open = True

    def handle_analysis_run(self, new_settings):
        self.settings = new_settings
        self.run_analysis()

    def generate_dummy_data(self, days=30):
        dates = pd.date_range(end=datetime.date.today(), periods=days)
        np.random.seed(42)
        trend = np.linspace(0, days, days)
        amounts = np.random.normal(50, 15, days) + trend
        amounts = np.maximum(amounts, 0)
        df = pd.DataFrame({'Date': dates, 'Amount': amounts})
        df['DateOrdinal'] = df['Date'].map(datetime.datetime.toordinal)
        return df

    def generate_insights(self, mean, std_dev, slope):
        insights = []
        if mean < 30: insights.append("You are maintaining a low daily spending average.")
        elif mean > 100: insights.append("Your average daily spending is quite high.")
        else: insights.append("Your daily spending is within a moderate range.")
        
        if std_dev < mean * 0.2: insights.append("Your spending is very consistent day-to-day.")
        elif std_dev > mean * 0.5: insights.append("Your spending varies significantly from day to day.")
        
        if slope > 0.5: insights.append("Warning: Your spending is trending upwards over time.")
        elif slope < -0.5: insights.append("Great job! Your spending is trending downwards.")
        
        return " ".join(insights)

    def run_analysis(self):
        try:
            selection = self.settings["date_range"]
            days = int(selection.split()[1])
            
            self.current_df = self.generate_dummy_data(days)
            df = self.current_df
            
            # Stats
            total_val = df['Amount'].sum()
            mean_val = df['Amount'].mean()
            median_val = df['Amount'].median()
            mode_val = df['Amount'].round(0).mode()[0] if not df['Amount'].mode().empty else 0
            std_dev = df['Amount'].std()
            
            self.stat_vars["Total"].set(f"${total_val:,.2f}")
            self.stat_vars["Mean"].set(f"${mean_val:.2f}")
            self.stat_vars["Median"].set(f"${median_val:.2f}")
            self.stat_vars["Mode"].set(f"${mode_val:.2f}")
            self.stat_vars["Std Dev"].set(f"${std_dev:.2f}")
            
            # Regression
            X = df['DateOrdinal'].values.reshape(-1, 1)
            y = df['Amount'].values
            model = LinearRegression()
            model.fit(X, y)
            
            last_date = df['DateOrdinal'].max()
            future_X = np.array([last_date + i for i in range(1, 8)]).reshape(-1, 1)
            future_y = model.predict(future_X)
            
            self.latest_model = model
            self.latest_future_X = future_X
            self.latest_future_y = future_y
            self.latest_std_dev = std_dev
            
            # Forecast Card
            pred_total = np.sum(future_y)
            pred_avg = np.mean(future_y)
            self.forecast_amount_label.configure(text=f"${pred_total:,.2f}")
            
            if pred_avg > mean_val * 1.05:
                self.forecast_trend_label.configure(text="TRENDING UP ↑", text_color="#FF5252")
                self.forecast_container.configure(border_color="#FF5252")
            elif pred_avg < mean_val * 0.95:
                self.forecast_trend_label.configure(text="TRENDING DOWN ↓", text_color="#69F0AE")
                self.forecast_container.configure(border_color="#69F0AE")
            else:
                self.forecast_trend_label.configure(text="STABLE →", text_color="#FFD740")
                self.forecast_container.configure(border_color="#FFD740")
                
            # Insights
            insight_text = self.generate_insights(mean_val, std_dev, model.coef_[0])
            self.insights_text.configure(state="normal")
            self.insights_text.delete("0.0", "end")
            self.insights_text.insert("0.0", insight_text)
            self.insights_text.configure(state="disabled")
            
            self.plot_graph()
            
            # Ensure sidebar is open to show results
            if not self.is_sidebar_open:
                self.toggle_sidebar()
                
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def plot_graph(self):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
            
        # Modern Dark Theme Colors
        bg_color = '#1E1E1E' # Darker background
        text_color = '#E0E0E0'
        grid_color = '#333333'
        accent_blue = '#4CC9F0'
        accent_pink = '#F72585'
        accent_purple = '#7209B7'
        
        fig, ax = plt.subplots(figsize=(6, 5), dpi=100)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        df = self.current_df
        model = self.latest_model
        
        scatter_hist = None
        scatter_fore = None
        
        # 1. Plot History (Actual Data)
        if self.settings["show_history"]:
            # Add fill under the curve for volume effect
            ax.fill_between(df['Date'], df['Amount'], color=accent_blue, alpha=0.1)
            # Plot line for continuity
            ax.plot(df['Date'], df['Amount'], color=accent_blue, alpha=0.4, linewidth=1.5, zorder=2)
            # Plot markers with white edge for pop
            scatter_hist = ax.scatter(df['Date'], df['Amount'], color=accent_blue, s=60, 
                                    edgecolors='white', linewidth=1.5, zorder=3, label='Actual')
            
        # 2. Plot Trend Line
        if self.settings["show_trend"]:
            X = df['DateOrdinal'].values.reshape(-1, 1)
            y_pred = model.predict(X)
            ax.plot(df['Date'], y_pred, color=accent_pink, linewidth=3, label='Trend', zorder=4)
            
            if self.settings["show_conf"]:
                ax.fill_between(df['Date'], y_pred - self.latest_std_dev, y_pred + self.latest_std_dev, 
                              color=accent_pink, alpha=0.15, zorder=1)
                
        # 3. Plot Forecast
        if self.settings["show_forecast"]:
            future_dates = [datetime.date.fromordinal(int(x[0])) for x in self.latest_future_X]
            
            scatter_fore = ax.scatter(future_dates, self.latest_future_y, color=accent_purple, 
                                    marker='o', s=70, edgecolors='white', linewidth=1.5, label='Forecast', zorder=3)
            ax.plot(future_dates, self.latest_future_y, color=accent_purple, linestyle='--', linewidth=2, alpha=0.8, zorder=2)
            
            if self.settings["show_conf"] and self.settings["show_trend"]:
                ax.fill_between(future_dates, self.latest_future_y - self.latest_std_dev, 
                              self.latest_future_y + self.latest_std_dev, color=accent_purple, alpha=0.15, zorder=1)

        # Styling
        title_text = f"Spending Analysis ({len(df)} Days)"
        if "Simulated" not in title_text: # Avoid duplication if logic changes
            title_text += "\n(Simulated Data)"
            
        ax.set_title(title_text, fontsize=16, color=text_color, pad=20, weight='bold')
        ax.set_xlabel("Date", fontsize=11, color=text_color, labelpad=10)
        ax.set_ylabel("Amount ($)", fontsize=11, color=text_color, labelpad=10)
        
        ax.tick_params(axis='x', colors=text_color, rotation=45, labelsize=9)
        ax.tick_params(axis='y', colors=text_color, labelsize=9)
        
        # Remove top and right spines for cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(grid_color)
        ax.spines['bottom'].set_color(grid_color)
        
        ax.grid(True, linestyle='--', alpha=0.2, color='white')
        
        # Legend
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            legend = ax.legend(loc='upper left', fontsize=10, frameon=False, labelcolor=text_color)
            
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        # Tooltips
        annot = ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="#333333", ec="gray", alpha=0.9),
                            color="white", fontsize=9, arrowprops=dict(arrowstyle="->", color="gray"))
        annot.set_visible(False)
        
        def update_annot(ind, sc, is_fore=False):
            pos = sc.get_offsets()[ind["ind"][0]]
            annot.xy = pos
            date_val = mdates.num2date(pos[0])
            text = f"{date_val.strftime('%b %d')}\n${pos[1]:.2f}" + ("\n(Forecast)" if is_fore else "")
            annot.set_text(text)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                if scatter_hist:
                    cont, ind = scatter_hist.contains(event)
                    if cont:
                        update_annot(ind, scatter_hist)
                        annot.set_visible(True)
                        canvas.draw_idle()
                        return
                if scatter_fore:
                    cont, ind = scatter_fore.contains(event)
                    if cont:
                        update_annot(ind, scatter_fore, True)
                        annot.set_visible(True)
                        canvas.draw_idle()
                        return
                if vis:
                    annot.set_visible(False)
                    canvas.draw_idle()
                    
        canvas.mpl_connect("motion_notify_event", hover)
        
        # Toolbar
        controls_frame = ctk.CTkFrame(self.graph_frame, fg_color="transparent")
        controls_frame.pack(fill="x", padx=10, pady=10)
        hidden_frame = ctk.CTkFrame(self.graph_frame, height=0, width=0)
        self.toolbar = NavigationToolbar2Tk(canvas, hidden_frame)
        self.toolbar.update()
        
        self.btn_reset = ctk.CTkButton(controls_frame, text="⟲ Reset", width=80, height=30, fg_color="#2B2B2B", border_width=1, border_color="gray50", command=self.toolbar.home)
        self.btn_reset.pack(side="left", padx=(0, 10))
        self.btn_pan = ctk.CTkButton(controls_frame, text="✋ Pan", width=80, height=30, fg_color="#2B2B2B", border_width=1, border_color="gray50", command=self.toggle_pan)
        self.btn_pan.pack(side="left", padx=(0, 10))
        self.btn_zoom = ctk.CTkButton(controls_frame, text="🔍 Zoom", width=80, height=30, fg_color="#2B2B2B", border_width=1, border_color="gray50", command=self.toggle_zoom)
        self.btn_zoom.pack(side="left", padx=(0, 10))
        self.btn_save = ctk.CTkButton(controls_frame, text="💾 Save", width=80, height=30, fg_color="#2B2B2B", border_width=1, border_color="gray50", command=self.toolbar.save_figure)
        self.btn_save.pack(side="right")

    def toggle_pan(self):
        self.toolbar.pan()
        if self.btn_pan.cget("fg_color") == "#2B2B2B":
            self.btn_pan.configure(fg_color="gray40", border_color="#3B8ED0")
            self.btn_zoom.configure(fg_color="#2B2B2B", border_color="gray50")
        else:
            self.btn_pan.configure(fg_color="#2B2B2B", border_color="gray50")

    def toggle_zoom(self):
        self.toolbar.zoom()
        if self.btn_zoom.cget("fg_color") == "#2B2B2B":
            self.btn_zoom.configure(fg_color="gray40", border_color="#3B8ED0")
            self.btn_pan.configure(fg_color="#2B2B2B", border_color="gray50")
        else:
            self.btn_zoom.configure(fg_color="#2B2B2B", border_color="gray50")

    def export_data(self):
        if self.current_df is None:
            messagebox.showwarning("No Data", "Please run analysis first.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if file_path:
            try:
                self.current_df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def toggle_pan(self):
        self.toolbar.pan()
        if self.btn_pan.cget("fg_color") == "#2B2B2B":
            self.btn_pan.configure(fg_color="gray40", border_color="#3B8ED0")
            self.btn_zoom.configure(fg_color="#2B2B2B", border_color="gray50") # Reset zoom
        else:
            self.btn_pan.configure(fg_color="#2B2B2B", border_color="gray50")

    def toggle_zoom(self):
        self.toolbar.zoom()
        if self.btn_zoom.cget("fg_color") == "#2B2B2B":
            self.btn_zoom.configure(fg_color="gray40", border_color="#3B8ED0")
            self.btn_pan.configure(fg_color="#2B2B2B", border_color="gray50") # Reset pan
        else:
            self.btn_zoom.configure(fg_color="#2B2B2B", border_color="gray50")

    def export_data(self):
        if self.current_df is None:
            messagebox.showwarning("No Data", "Please run the analysis first.")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                                                 title="Export Prediction Data")
        if file_path:
            try:
                self.current_df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Data exported successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data:\n{e}")
