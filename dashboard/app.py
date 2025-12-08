import customtkinter as ctk;
class DashboardView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.label = ctk.CTkLabel(self, text="Dashboard View", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=20)

        # Example content
        self.info_label = ctk.CTkLabel(self, text="Welcome to your financial overview.")
        self.info_label.grid(row=1, column=0, padx=20, pady=10)
