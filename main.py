import customtkinter as ctk

# Import Views
from dashboard.app import DashboardView
from transaction.manager import TransactionView
from analytics.analytics import AnalyticsView
from predictions.model import PredictionsView

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class FinanceTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Finance Tracker App")
        self.geometry("1100x700")

        # Configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Finance Tracker", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sidebar_button_1 = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.sidebar_button_event_dashboard)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        
        self.sidebar_button_2 = ctk.CTkButton(self.sidebar_frame, text="Transactions", command=self.sidebar_button_event_transactions)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        
        self.sidebar_button_3 = ctk.CTkButton(self.sidebar_frame, text="Analytics", command=self.sidebar_button_event_analytics)
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        
        self.sidebar_button_4 = ctk.CTkButton(self.sidebar_frame, text="Predictions", command=self.sidebar_button_event_predictions)
        self.sidebar_button_4.grid(row=4, column=0, padx=20, pady=10)

        self.sidebar_button_exit = ctk.CTkButton(self.sidebar_frame, text="Exit", command=self.sidebar_button_event_exit, fg_color="#c42b1c", hover_color="#8a1f15")
        self.sidebar_button_exit.grid(row=6, column=0, padx=20, pady=(10, 20))

        # Initialize Views
        self.dashboard_view = DashboardView(self)
        self.transaction_view = TransactionView(self)
        self.analytics_view = AnalyticsView(self)
        self.predictions_view = PredictionsView(self)

        # Select default frame
        self.select_frame_by_name("dashboard")

        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start maximized (Full Screen)
        self.after(0, lambda: self.state('zoomed'))

    def select_frame_by_name(self, name):
        # set button color for selected button
        self.sidebar_button_1.configure(fg_color=("gray75", "gray25") if name == "dashboard" else "transparent")
        self.sidebar_button_2.configure(fg_color=("gray75", "gray25") if name == "transactions" else "transparent")
        self.sidebar_button_3.configure(fg_color=("gray75", "gray25") if name == "analytics" else "transparent")
        self.sidebar_button_4.configure(fg_color=("gray75", "gray25") if name == "predictions" else "transparent")

        # show selected frame
        if name == "dashboard":
            self.dashboard_view.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=20, pady=20)
        else:
            self.dashboard_view.grid_forget()
            
        if name == "transactions":
            self.transaction_view.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=20, pady=20)
        else:
            self.transaction_view.grid_forget()
            
        if name == "analytics":
            self.analytics_view.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=20, pady=20)
        else:
            self.analytics_view.grid_forget()
            
        if name == "predictions":
            self.predictions_view.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=20, pady=20)
        else:
            self.predictions_view.grid_forget()

    def sidebar_button_event_dashboard(self):
        self.select_frame_by_name("dashboard")

    def sidebar_button_event_transactions(self):
        self.select_frame_by_name("transactions")

    def sidebar_button_event_analytics(self):
        self.select_frame_by_name("analytics")
        
    def sidebar_button_event_predictions(self):
        self.select_frame_by_name("predictions")

    def sidebar_button_event_exit(self):
        self.on_closing()
        
    def on_closing(self):
        self.withdraw()
        self.quit()

if __name__ == "__main__":
    app = FinanceTrackerApp()
    app.mainloop()
