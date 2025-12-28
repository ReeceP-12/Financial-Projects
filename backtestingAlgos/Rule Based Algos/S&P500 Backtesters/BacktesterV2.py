import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# 1. DATA ACQUISITION
data = yf.download("SPY", start="2010-01-10")

# Flatten MultiIndex if present (yfinance sometimes returns ticker as top level)
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

data.dropna(inplace=True)

# 2. FEATURE ENGINEERING
data["SMA_10"] = data["Close"].rolling(window=10).mean()
data["SMA_50"] = data["Close"].rolling(window=50).mean()

# RSI Calculation
data["Change"] = data["Close"].diff()
data["Gain"] = np.where(data["Change"] > 0, data["Change"], 0)
data["Loss"] = np.where(data["Change"] < 0, abs(data["Change"]), 0)
data["Avg_Gain"] = data["Gain"].ewm(com=13, min_periods=14).mean()
data["Avg_Loss"] = data["Loss"].ewm(com=13, min_periods=14).mean()
data["RS"] = data["Avg_Gain"] / data["Avg_Loss"]
data["RSI"] = 100 - (100 / (1 + data["RS"]))

# 3. SIGNAL GENERATION
data["Signal"] = np.where((data["SMA_10"] > data["SMA_50"]) & (data["RSI"] < 70), 1.0, 0.0)

# 4. BACKTESTING ENGINE
data["Market_returns"] = data["Close"].pct_change()
data["Strategy_returns"] = data["Market_returns"] * data["Signal"].shift(1)
data["Cumulative_market"] = (1 + data["Market_returns"].fillna(0)).cumprod()
data["Cumulative_strategy"] = (1 + data["Strategy_returns"].fillna(0)).cumprod()

# 5. RISK METRICS
std = data["Strategy_returns"].std()
if std > 0:
    sharpe = (data["Strategy_returns"].mean() / std) * math.sqrt(252)
else:
    sharpe = 0

#max dd
data["Peak"] = data["Cumulative_strategy"].cummax()
data["Drawdown"] = (data["Cumulative_strategy"] / data["Peak"]) - 1
max_dd = data["Drawdown"].min()

# 6. OUTPUT
# Added .fillna(0) to iloc calls to prevent errors if data is empty
print(f"Final Strategy return: {data['Cumulative_strategy'].iloc[-1]:.2f}x")
print(f"Final Market return: {data['Cumulative_market'].iloc[-1]:.2f}x")
print(f"Max Drawdown: {max_dd * 100:.2f}%") # Multiply by 100 for percentage
print(f"Sharpe Ratio: {sharpe:.2f}")

# Visualisation
plt.figure(figsize=(12, 6))
plt.plot(data["Cumulative_strategy"], label="Strategy")
plt.plot(data["Cumulative_market"], label="Market", alpha=0.5)
plt.legend()
plt.title("SPY Strategy Backtest")
plt.show()
