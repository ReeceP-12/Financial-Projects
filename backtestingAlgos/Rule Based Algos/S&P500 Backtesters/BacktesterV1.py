import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# Download the dataset
data = yf.download("SPY", start="2010-01-10")
data.info()
# Removing all rows with missing values
data.dropna(inplace=True)

# calculate 10 day SMA - fast
data["SMA_10"] = data["Close"].rolling(window=10).mean()
# calculate 50 day SMA - slow
data["SMA_50"] = data["Close"].rolling(window=50).mean()
# remove all rows that now come up with missing values
data.dropna(inplace=True)

# SMA crossover rule - determine a bullish trend as fast SMA on average is higher than slower SMA
# This is the PRIMARY signal for Prototype 1
data["Position"] = np.where(data["SMA_10"] > data["SMA_50"], 1.0, 0.0)

# calculates the percentage change in close values, today and yesterday
data["daily_returns"] = data["Close"].pct_change()



# avoid look ahead bias - uses current days close value instead of tomorrow's close value
data["strategy_returns"] = (data["daily_returns"] * data["Position"].shift(1))
# calculates compound returns, adds one to create a percentage, like * by 100
data["cumulative_returns"] = (data["strategy_returns"] + 1).cumprod()
print(data[0:100].to_string())

# Benchmarking data
# buying and holding for the entire duration
data["buy_hold_returns"] = (data["daily_returns"] + 1).cumprod()

# Annual Sharpe Ratio Calculations
mean_dr = data["strategy_returns"].mean()
std_dr = data["strategy_returns"].std()
daily_sharpe = mean_dr / std_dr
annual_sharpe = daily_sharpe * math.sqrt(252)

# Maximum Drawdown Implementation
data["Running_max"] = data["cumulative_returns"].cummax()
# Calculate the Drawdown from the peak (percentage loss)
data["Drawdown"] = (data["cumulative_returns"] / data["Running_max"]) - 1
max_dd = data["Drawdown"].min()

# -------------------------------------------------------------
# PROTOTYPE 1 RESULTS OUTPUT
# -------------------------------------------------------------
print("\n--- Prototype 1 (Simple SMA) Results ---")
print(f"Annual Sharpe Ratio: {annual_sharpe:.2f}")
print(f"Maximum Drawdown: {max_dd * 100:.2f}%")
print(f"Final Cumulative Return: {data['cumulative_returns'].iloc[-1]:.2f}x")

# Plotting for visual evidence
plt.figure(figsize=(12, 6))
data["cumulative_returns"].plot(label="SMA Strategy")
data["buy_hold_returns"].plot(label="Buy & Hold Benchmark")
plt.title("Prototype 1: Simple SMA Strategy vs. Buy & Hold")
plt.xlabel("Date")
plt.ylabel("Cumulative Returns")
plt.legend()
plt.grid(True)
plt.show()
