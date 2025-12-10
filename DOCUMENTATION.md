# Finance Tracker Application Documentation

This project is a comprehensive Finance Tracker application built with Python. It features a modern graphical user interface (GUI), database persistence, and advanced analytics including predictive modeling.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Features Overview](#features-overview)
3. [Technical Implementation Checklist](#technical-implementation-checklist)
4. [Module Breakdown](#module-breakdown)
5. [How to Run](#how-to-run)
6. [Dependencies](#dependencies)

---

## Project Structure

```
FINALS/
├── main.py                 # Application entry point
├── transactions.db         # SQLite database file
├── requirements.txt        # Python dependencies
├── seed_data.py            # Script to populate sample data
├── DOCUMENTATION.md        # This file
├── dashboard/
│   ├── __init__.py
│   └── app.py              # DashboardView class and DB utilities
├── transaction/
│   ├── __init__.py
│   └── manager.py          # TransactionView, Transaction model, iterators
├── analytics/
│   ├── __init__.py
│   └── analytics.py        # AnalyticsView with charts and KPIs
└── predictions/
    ├── __init__.py
    └── model.py            # PredictionsView with ML forecasting
```

---

## Features Overview

### Dashboard Tab
- **Summary Cards**: Total Income, Total Expenses, Net Balance, Transaction Count
- **Spending Distribution Chart**: Pie chart showing category breakdown
- **Recent Activity**: List of latest transactions
- **Quick Actions**: Refresh and Clear Data buttons

### Transactions Tab
- **Full CRUD Operations**: Add, Edit, Delete transactions
- **Advanced Filtering**:
  - By **Date/Month**: All Time, This Month, Last Month, Last 3 Months
  - By **Type**: Income, Expense, All Types
  - By **Category**: Dynamic list based on existing data
- **Search**: Real-time text search across all fields
- **Export**: Export filtered data to CSV
- **Live Stats**: Transaction count, total income, total expenses (filtered)

### Analytics Tab
- **Advanced KPIs**:
  - Savings Rate (All Time)
  - Average Daily Spend
  - Monthly Variability (Standard Deviation)
  - Largest Single Expense
- **Chart Views**:
  - **Wealth Trajectory**: Cumulative balance over time with trend line
  - **Categorical Trends**: Top spending categories over months (stacked area)

### Predictions Tab
- **Machine Learning Forecasting**: Uses Linear Regression to predict future spending
- **7-Day Forecast**: Projected total spend for the coming week
- **Trend Indicators**: Shows if spending is trending UP, DOWN, or STABLE
- **Statistical Metrics**: Total, Mean, Median, Mode, Standard Deviation
- **AI Insights**: Auto-generated spending advice based on patterns
- **Interactive Chart**: Toggle history, trend line, forecast, and confidence bands

---

## Technical Implementation Checklist

This application incorporates the following technical concepts as per the course requirements:

### 1. Core Python Concepts

| Concept | Description | Location |
|---------|-------------|----------|
| **Casting** | Type conversions for amounts and IDs | `transaction/manager.py` - `Transaction.__init__` |
| **Collections** | Lists, tuples, sets, dictionaries throughout | `TransactionCollection`, `cols` dict in `TransactionView` |
| **String Modification** | `.strip()`, `.title()`, `.upper()`, formatting | `Transaction.__init__` - `description.strip().title()` |
| **User Input** | GUI forms with validation | `TransactionView._open_modal` |
| **Control Flow** | if/elif/else logic for categorization | `analytics.py` savings rate, `manager.py` filtering |
| **Loops** | for loops for data processing | `load_table_from_db` in `manager.py` |
| **F-strings** | `f"₱{amount:.2f}"` formatting everywhere | All modules |

#### Code Examples:

**Casting:**
```python
# transaction/manager.py - Transaction class
self.id = int(tid)          # Casting to integer
self.amount = float(amount)  # Casting to float
```

**String Modification:**
```python
# transaction/manager.py - Transaction class
self.description = description.strip().title()  # Removes whitespace, capitalizes
self.category = category.strip().title()
```

**Control Flow:**
```python
# analytics/analytics.py
if total_income > 0:
    savings_rate = ((total_income - total_expense) / total_income) * 100
else:
    savings_rate = 0.0
```

**F-strings with Placeholders & Modifiers:**
```python
# dashboard/app.py
self.card_income.configure(text=f"₱{s['income']:,.2f}")  # Formatted currency
```

---

### 2. Functions & Lambdas

| Concept | Description | Location |
|---------|-------------|----------|
| **Lambda Functions** | Filtering, sorting, mapping operations | `analytics/analytics.py` |
| **Placeholders & Modifiers** | `.format()` and format specifiers | SQL queries, f-strings |

#### Code Examples:

**Lambda Functions:**
```python
# analytics/analytics.py
df['income'] = df['amount'].apply(lambda x: x if x > 0 else 0)
df['expense'] = df['amount'].apply(lambda x: abs(x) if x < 0 else 0)
```

**Placeholders in SQL:**
```python
# dashboard/app.py
cur.execute("""
    INSERT INTO transactions (date, description, amount, category)
    VALUES (?, ?, ?, ?)""",
    (date, description, amount, category))
```

---

### 3. Object-Oriented Programming (OOP)

| Concept | Description | Location |
|---------|-------------|----------|
| **Classes & Objects** | `Transaction`, `Income`, `Expense` classes | `transaction/manager.py` |
| **`__init__` and `__str__`** | Object initialization and representation | `Transaction` class |
| **Object Methods** | Instance methods with business logic | `to_dict()`, `load_table_from_db()` |
| **Self Parameter** | Throughout all class methods | All view classes |
| **Inheritance** | `Income` and `Expense` extend `Transaction` | `transaction/manager.py` |
| **Parent/Child Classes** | Proper `super()` usage | `Income.__init__`, `Expense.__init__` |
| **Iterators** | Custom `TransactionIterator` and `__iter__`/`__next__` | `TransactionCollection` |

#### Code Examples:

**Classes & Objects with `__init__` and `__str__`:**
```python
# transaction/manager.py
class Transaction:
    def __init__(self, tid: int, date: str, description: str, amount: float, category: str = "General"):
        self.id = int(tid)
        self.date = str(date)
        self.description = description.strip().title()
        self.amount = float(amount)
        self.category = category.strip().title()

    def __str__(self):
        return f"Transaction(id={self.id}, date={self.date}, desc='{self.description}', amount={self.amount:.2f})"
```

**Inheritance with Parent/Child Classes:**
```python
# transaction/manager.py
class Income(Transaction):
    def __init__(self, tid, date, description, amount, source="Salary"):
        super().__init__(tid, date, description, amount, category="Income")
        self.source = source

class Expense(Transaction):
    def __init__(self, tid, date, description, amount, merchant="Unknown"):
        super().__init__(tid, date, description, amount, category="Expense")
        self.merchant = merchant
```

**Iterators:**
```python
# transaction/manager.py
class TransactionCollection(Iterable):
    def __init__(self, transactions: List[Transaction] = None):
        self._transactions = list(transactions) if transactions else []

    def __iter__(self) -> Iterator[Transaction]:
        return iter(self._transactions)
```

---

### 4. Data Science & Advanced Libraries

| Concept | Description | Location |
|---------|-------------|----------|
| **Database** | SQLite with CRUD operations | `transactions.db`, `manager.py`, `app.py` |
| **NumPy** | Array operations for analytics | `predictions/model.py`, `analytics.py` |
| **Arrays** | NumPy arrays for statistical calculations | `linear_regression_predict()` |
| **Matplotlib** | Multiple chart types embedded in GUI | `analytics.py`, `model.py` |
| **Statistics Module** | Mean, median, mode, stdev | `compute_stats()` in `manager.py` |
| **SciPy** | Advanced stats (skew, kurtosis) | `stats.mode()` fallback |
| **Machine Learning** | Linear regression with sklearn/scipy | `predictions/model.py` |
| **Mean/Median/Mode/StdDev** | Complete statistical analysis | `PredictionsView.run_analysis()` |
| **Linear Regression** | Predictive modeling for spending trends | `sklearn.linear_model.LinearRegression` |

#### Code Examples:

**Database Operations:**
```python
# dashboard/app.py
def fetch_summary():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT SUM(amount) as total FROM transactions WHERE amount>0")
    income = cur.fetchone()["total"] or 0.0
    # ... more queries
    return {"income": income, "expenses": expenses, "net": net, "count": cnt}
```

**NumPy Arrays:**
```python
# transaction/manager.py
def linear_regression_predict(amounts: List[float], predict_steps: int = 1):
    arr = np.array(amounts, dtype=float)  # Convert to NumPy array
    x = np.arange(len(arr))
    coeffs = np.polyfit(x, arr, deg=1)    # Linear regression
    # ...
```

**Statistics Module:**
```python
# transaction/manager.py
import statistics as stats_stdlib

def compute_stats(data: List[float]):
    mean = stats_stdlib.mean(data)
    median = stats_stdlib.median(data)
    mode = stats_stdlib.mode(data)
    stdev = stats_stdlib.stdev(data) if len(data) > 1 else 0.0
    return {"mean": mean, "median": median, "mode": mode, "stdev": stdev}
```

**Machine Learning - Linear Regression:**
```python
# predictions/model.py
from sklearn.linear_model import LinearRegression

model = LinearRegression()
X = df['DateOrdinal'].values.reshape(-1, 1)
y = df['Amount'].values
model.fit(X, y)

# Predict future values
future_y = model.predict(future_X)
```

**Matplotlib Charts:**
```python
# analytics/analytics.py
def _plot_wealth_trajectory(self, ax, df):
    df['cumulative_balance'] = df['amount'].cumsum()
    ax.plot(df['date'], df['cumulative_balance'], color='#4CC9F0', linewidth=2)
    ax.fill_between(df['date'], df['cumulative_balance'], alpha=0.1, color='#4CC9F0')
    ax.set_title("Wealth Accumulation Trajectory", fontsize=14, color='white')
```

---

## Module Breakdown

### `main.py`
The application entry point. Creates the main window using `customtkinter` and sets up the tabbed interface with all four views.

### `dashboard/app.py`
- **DashboardView**: Main overview panel
- **Database Utilities**: `get_conn()`, `init_db()`, `insert_transaction()`, `fetch_transactions()`, `fetch_summary()`, `fetch_category_breakdown()`, `clear_all_data()`
- **UI Components**: Summary cards, pie chart, recent transactions list

### `transaction/manager.py`
- **TransactionView**: Full transaction management UI
- **Transaction**: Base data model class
- **Income/Expense**: Inherited specialized classes
- **TransactionCollection**: Iterable collection with iterator
- **Helper Functions**: `load_transactions_from_db()`, `save_transaction_db()`, `compute_stats()`, `linear_regression_predict()`

### `analytics/analytics.py`
- **AnalyticsView**: Deep-dive analysis panel
- **KPI Calculations**: Savings rate, daily average, volatility, largest expense
- **Charts**: Wealth trajectory (line), category trends (stacked area)

### `predictions/model.py`
- **PredictionsView**: ML-powered forecasting panel
- **AnalysisSettingsModal**: Configuration dialog for analysis parameters
- **Forecasting**: 7-day spending prediction using Linear Regression
- **Insights**: Auto-generated textual advice based on spending patterns

---

## How to Run

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. (Optional) Seed Sample Data
```bash
python seed_data.py
```

### 3. Start the Application
```bash
python main.py
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern GUI framework |
| `pandas` | Data manipulation and analysis |
| `numpy` | Numerical computing |
| `matplotlib` | Chart visualization |
| `scikit-learn` | Machine learning (Linear Regression) |
| `scipy` | Scientific computing (statistics) |

---

## Database Schema

**Table: `transactions`**
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `date` | TEXT | Transaction date (YYYY-MM-DD) |
| `description` | TEXT | Transaction description |
| `amount` | REAL | Amount (positive = income, negative = expense) |
| `category` | TEXT | Category name |

---

## Currency

The application uses the **Philippine Peso (₱)** as the default currency symbol throughout all displays.

---

## Authors

Developed as a Python programming project demonstrating comprehensive use of:
- Core Python concepts
- Object-Oriented Programming
- Data Science libraries
- Machine Learning
- GUI development

---

*Last Updated: December 2024*
