"""
Personal Finance Tracker - Analytics Module
Demonstrates: NumPy, SciPy, Statistics, Machine Learning, Linear Regression
"""
import numpy as np
from scipy import stats
import statistics
try:
    from sklearn.linear_model import LinearRegression  # type: ignore
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    LinearRegression = None  # type: ignore
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from finance_core import Transaction, Expense, Income


class FinanceAnalyzer:
    """Statistical and predictive analysis for finance data"""
    
    @staticmethod
    def calculate_statistics(amounts: List[float]) -> Dict:
        """Calculate mean, median, mode, standard deviation"""
        if not amounts:
            return {
                'mean': 0, 'median': 0, 'mode': 0, 
                'std_dev': 0, 'min': 0, 'max': 0
            }
        
        # Using statistics module
        mean_val = statistics.mean(amounts)
        median_val = statistics.median(amounts)
        
        try:
            mode_val = statistics.mode(amounts)
        except statistics.StatisticsError:
            mode_val = amounts[0] if amounts else 0
        
        std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        return {
            'mean': round(mean_val, 2),
            'median': round(median_val, 2),
            'mode': round(mode_val, 2),
            'std_dev': round(std_dev, 2),
            'min': round(min(amounts), 2),
            'max': round(max(amounts), 2)
        }
    
    @staticmethod
    def scipy_analysis(amounts: List[float]) -> Dict:
        """Advanced scipy statistics"""
        if len(amounts) < 3:
            return {'skewness': 0, 'kurtosis': 0}
        
        array = np.array(amounts)
        return {
            'skewness': float(stats.skew(array)),
            'kurtosis': float(stats.kurtosis(array))
        }
    
    @staticmethod
    def numpy_operations(amounts: List[float]) -> Dict:
        """NumPy array operations"""
        if not amounts:
            return {'sum': 0, 'mean': 0, 'percentile_75': 0}
        
        arr = np.array(amounts)
        return {
            'sum': float(np.sum(arr)),
            'mean': float(np.mean(arr)),
            'percentile_25': float(np.percentile(arr, 25)),
            'percentile_75': float(np.percentile(arr, 75)),
            'cumulative_sum': np.cumsum(arr).tolist()
        }
    
    @staticmethod
    def predict_spending(transactions: List[Transaction], days_ahead: int = 30) -> Dict:
        """
        Linear regression to predict future spending
        Machine Learning demonstration
        """
        expenses = [t for t in transactions if isinstance(t, Expense)]
        
        if len(expenses) < 2:
            return {
                'prediction': 0,
                'daily_rate': 0,
                'r_squared': 0,
                'days_ahead': days_ahead
            }
        
        # Sort by date and create time series
        expenses.sort(key=lambda x: x.date)
        
        # Convert dates to days since first transaction
        first_date = datetime.fromisoformat(expenses[0].date)
        X = []
        y = []
        
        for exp in expenses:
            exp_date = datetime.fromisoformat(exp.date)
            days_diff = (exp_date - first_date).days
            X.append([days_diff])
            y.append(exp.amount)
        
        # Train linear regression model
        X_array = np.array(X)
        y_array = np.array(y)
        
        if HAS_SKLEARN and LinearRegression is not None:
            model = LinearRegression()
            model.fit(X_array, y_array)
            
            # Predict future
            last_day = X[-1][0]
            future_day = last_day + days_ahead
            prediction = model.predict(np.array([[future_day]]))[0]
            
            # Calculate R² score
            r_squared = model.score(X_array, y_array)
            coef = model.coef_[0]
        else:
            # Manual linear regression using scipy
            X_flat = X_array.flatten()
            slope, intercept, r_value, p_value, std_err = stats.linregress(X_flat, y_array)  # type: ignore
            
            last_day = X[-1][0]
            future_day = last_day + days_ahead
            prediction = slope * future_day + intercept  # type: ignore
            r_squared = r_value * r_value  # type: ignore
            coef = slope  # type: ignore
        
        return {
            'prediction': round(float(prediction), 2),  # type: ignore
            'daily_rate': round(float(coef), 2),  # type: ignore
            'r_squared': round(float(r_squared), 3),  # type: ignore
            'days_ahead': days_ahead
        }
    
    @staticmethod
    def monthly_trend(transactions: List[Transaction]) -> Tuple[List[str], List[float], List[float]]:
        """
        Calculate monthly income and expense trends
        Returns: (months, income_amounts, expense_amounts)
        """
        from collections import defaultdict
        
        income_by_month = defaultdict(float)
        expense_by_month = defaultdict(float)
        
        for t in transactions:
            month = t.date[:7]  # YYYY-MM format
            if isinstance(t, Income):
                income_by_month[month] += t.amount
            else:
                expense_by_month[month] += t.amount
        
        # Get sorted months
        all_months = sorted(set(list(income_by_month.keys()) + list(expense_by_month.keys())))
        
        income_vals = [income_by_month[m] for m in all_months]
        expense_vals = [expense_by_month[m] for m in all_months]
        
        return all_months, income_vals, expense_vals
    
    @staticmethod
    def category_percentages(transactions: List[Transaction]) -> Dict[str, float]:
        """Calculate percentage of spending by category"""
        expenses = [t for t in transactions if isinstance(t, Expense)]
        
        if not expenses:
            return {}
        
        # Using lambda and sum
        total = sum(map(lambda x: x.amount, expenses))
        
        from collections import defaultdict
        category_totals = defaultdict(float)
        
        for exp in expenses:
            category_totals[exp.category] += exp.amount
        
        # Calculate percentages with f-strings and placeholders
        percentages = {
            category: round((amount / total) * 100, 1)
            for category, amount in category_totals.items()
        }
        
        return dict(sorted(percentages.items(), key=lambda x: x[1], reverse=True))
