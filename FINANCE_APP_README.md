 # Personal Finance Tracker

A complete desktop application demonstrating all Python concepts in a practical, usable tool.

## Features

### 💰 Track Your Finances
- Record income and expenses with categories
- View transaction history with filtering
- Real-time balance calculations
- SQLite database for persistent storage

### 📊 Data Visualization
- Category spending pie charts
- Monthly income vs expense trends
- Statistical distribution histograms
- Interactive matplotlib charts

### 📈 Analytics & Statistics
- Mean, median, mode calculations
- Standard deviation analysis
- NumPy array operations
- SciPy statistical measures (skewness, kurtosis)
- Percentile analysis

### 🤖 Machine Learning Predictions
- Linear regression spending forecasts
- Predictive analytics for future expenses
- Model confidence scores (R² values)
- Daily spending rate trends

## Python Concepts Demonstrated

✅ **Casting** - Type conversions for amounts and IDs  
✅ **Collections** - Lists, tuples, sets, dictionaries throughout  
✅ **String Modification** - `.strip()`, `.title()`, `.upper()`, formatting  
✅ **User Input** - GUI forms with validation  
✅ **Control Flow** - if/elif/else logic for categorization  
✅ **Loops** - for loops for data processing  
✅ **F-strings** - `f"${amount:.2f}"` formatting everywhere  
✅ **Placeholders & Modifiers** - `.format()` and format specifiers  
✅ **Lambda Functions** - Filtering, sorting, mapping operations  
✅ **Classes & Objects** - `Transaction`, `Income`, `Expense` classes  
✅ **__init__ and __str__** - Object initialization and representation  
✅ **Object Methods** - Instance methods with business logic  
✅ **Self Parameter** - Throughout all class methods  
✅ **Inheritance** - `Income` and `Expense` extend `Transaction`  
✅ **Parent/Child Classes** - Proper `super()` usage  
✅ **Iterators** - Custom `TransactionIterator` and `__iter__`/`__next__`  
✅ **Database** - SQLite with CRUD operations  
✅ **NumPy** - Array operations for analytics  
✅ **Arrays** - NumPy arrays for statistical calculations  
✅ **Matplotlib** - Multiple chart types embedded in GUI  
✅ **Statistics Module** - Mean, median, mode, stdev  
✅ **SciPy** - Advanced stats (skew, kurtosis)  
✅ **Machine Learning** - Linear regression with sklearn/scipy  
✅ **Mean/Median/Mode/StdDev** - Complete statistical analysis  
✅ **Linear Regression** - Predictive modeling for spending trends  

## Installation

Ensure dependencies are installed:

```powershell
pip install -r requirements.txt
```

## Running the Application

Launch the finance tracker:

```powershell
python finance_app.py
```

## Quick Start Guide

### 1. Dashboard Tab
- View your financial summary (income, expenses, net balance)
- See category breakdown pie chart
- Quick actions: Add sample data to test features

### 2. Add Transaction Tab
- Enter income or expense details
- Amount, category, description, date
- Automatic balance updates

### 3. Transactions Tab
- View all transactions in a sortable table
- Filter by category using dropdown
- Delete transactions with confirmation

### 4. Analytics Tab
- Generate three types of charts:
  - **Category Pie Chart**: Spending distribution
  - **Monthly Trend**: Income vs expenses over time
  - **Statistics**: Histogram with mean/median lines
- View detailed statistics (mean, median, mode, standard deviation)
- NumPy and SciPy analysis results

### 5. Predictions Tab
- Set prediction timeframe (1-365 days)
- Get ML-powered spending forecast
- View model confidence and daily rate trends
- Automatic interpretation of results

## Sample Workflow

1. Click "Add Sample Data" on Dashboard to populate test transactions
2. Go to "Transactions" tab to see all entries
3. Try filtering by category (e.g., "Food")
4. Open "Analytics" tab and generate different charts
5. View statistical analysis in the output area
6. Go to "Predictions" tab and forecast spending 30 days ahead
7. Observe the linear regression results and confidence score

## Database

- Uses SQLite (`finance_app.db` created automatically)
- Persistent storage across sessions
- JSON encoding for extended attributes
- CRUD operations demonstrated

## Architecture

```
finance_app.py       - Main GUI application (Tkinter)
finance_core.py      - Data models, classes, inheritance, database
finance_analytics.py - Statistics, NumPy, SciPy, ML predictions
```

## Tips

- Start with sample data to see all features
- Try different chart types in Analytics
- Higher transaction count = better ML predictions
- R² score above 0.8 indicates strong trend
- Use category filtering for targeted analysis

## Educational Value

This is a **fully functional application** that demonstrates every required Python concept in a practical context, not just isolated examples. Every feature serves the user while showcasing programming principles.
