import customtkinter as ctk

class TransactionView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.label = ctk.CTkLabel(self, text="Transaction Management", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=20)
        
        # Example content
        self.add_btn = ctk.CTkButton(self, text="Add Transaction")
        self.add_btn.grid(row=1, column=0, padx=20, pady=10)
