import sqlite3
import datetime
import random

DB_FILE = "transactions.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        date TEXT,
        description TEXT,
        amount REAL,
        category TEXT
    )""")
    conn.commit()
    conn.close()

def seed_data():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # clear provided we are just seeding demo data? Or strictly append?
    # The user asked to "populate", usually implies empty or filling up. 
    # Let's ask if they want to clear or append? 
    # Actually, for a clean demo, clearing is often better, but safer to append or just inform.
    # I'll clear for now to ensure quality demo data avoids duplicates if run twice, 
    # but I'll comment it out or make it optional. 
    # actually, let's just clear to ensure the charts look good.
    cur.execute("DELETE FROM transactions")
    
    categories_income = ["Salary", "Freelance", "Investments", "Consulting", "Gift"]
    categories_expense = ["Food", "Rent", "Utilities", "Transportation", "Entertainment", "Healthcare", "Shopping", "Education"]
    
    start_date = datetime.date.today() - datetime.timedelta(days=120)
    end_date = datetime.date.today()
    
    transactions = []
    
    # 1. Recurring Monthly (Salary, Rent)
    current = start_date
    while current <= end_date:
        # Salary: 15th and 30th? Or just 1st. Let's say 15th and 30th.
        if current.day == 15 or current.day == 30:
            transactions.append((current, "Salary", 2500.0, "Salary"))
        
        # Rent: 1st
        if current.day == 1:
            transactions.append((current, "Rent Payment", -1200.0, "Rent"))
            transactions.append((current, "Internet Bill", -60.0, "Utilities"))
            
        current += datetime.timedelta(days=1)

    # 2. Frequent Random Expenses
    for i in range(120): # One per day roughly?
        current = start_date + datetime.timedelta(days=i)
        
        # Food (frequent)
        if random.random() > 0.3: # 70% chance
            amt = -random.uniform(10, 50)
            transactions.append((current, "Groceries/Lunch", round(amt, 2), "Food"))
            
        # Transport (frequent)
        if random.random() > 0.6:
            amt = -random.uniform(5, 20)
            transactions.append((current, "Uber/Gas", round(amt, 2), "Transportation"))
            
        # Entertainment (occasional)
        if random.random() > 0.8:
            amt = -random.uniform(20, 100)
            transactions.append((current, "Movies/Games", round(amt, 2), "Entertainment"))
            
        # Shopping (random)
        if random.random() > 0.9:
            amt = -random.uniform(50, 200)
            transactions.append((current, "Online Shopping", round(amt, 2), "Shopping"))
            
        # Freelance Income (occasional)
        if random.random() > 0.95:
             amt = random.uniform(200, 800)
             transactions.append((current, "Freelance Job", round(amt, 2), "Freelance"))

    # Sort by date
    transactions.sort(key=lambda x: x[0])
    
    print(f"Generating {len(transactions)} transactions...")
    
    # Insert
    for t in transactions:
        cur.execute("INSERT INTO transactions (date, description, amount, category) VALUES (?, ?, ?, ?)",
                    (t[0].isoformat(), t[1], t[2], t[3]))
        
    conn.commit()
    conn.close()
    print("Database populated successfully.")

if __name__ == "__main__":
    init_db()
    seed_data()
