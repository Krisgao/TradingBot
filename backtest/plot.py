import os
import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import ta

from config import API_KEY, API_SECRET
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 设置为微软雅黑等支持中文的字体
matplotlib.rcParams['axes.unicode_minus'] = False
client = StockHistoricalDataClient(API_KEY, API_SECRET)

def backtest_and_plot(symbol, days=90, save_dir="backtest"):
    # 1. 获取历史数据
    end = datetime.now()
    start = end - timedelta(days=days)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )

    bars = client.get_stock_bars(request).df

    if bars.empty:
        print("❌ 没有拿到历史数据")
        return

    df = bars[bars.index.get_level_values(0) == symbol].copy()
    df.reset_index(inplace=True)

    df["sma"] = df["close"].rolling(window=20).mean()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

    # 2. 回测逻辑（与 HybridStrategy 一致）
    position = False
    buy_dates, sell_dates = [], []
    buy_prices, sell_prices = [], []

    for i in range(len(df)):
        price = df.loc[i, "close"]
        sma = df.loc[i, "sma"]
        rsi = df.loc[i, "rsi"]

        if pd.isna(sma) or pd.isna(rsi):
            continue

        if not position and price > sma and rsi < 30:
            position = True
            buy_dates.append(df.loc[i, "timestamp"])
            buy_prices.append(price)

        elif position and price < sma and rsi > 70:
            position = False
            sell_dates.append(df.loc[i, "timestamp"])
            sell_prices.append(price)

    # 3. 绘图
    plt.figure(figsize=(14, 6))
    plt.plot(df["timestamp"], df["close"], label="价格", color="blue")
    plt.plot(df["timestamp"], df["sma"], label="SMA(20)", linestyle="--", color="gray")
    plt.scatter(buy_dates, buy_prices, marker="^", color="green", label="BUY", s=100)
    plt.scatter(sell_dates, sell_prices, marker="v", color="red", label="SELL", s=100)

    plt.title(f"{symbol} 回测图表（Hybrid策略）")
    plt.xlabel("时间")
    plt.ylabel("价格")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # 保存图像
    os.makedirs(save_dir, exist_ok=True)
    filepath = f"{save_dir}/{symbol}_backtest.png"
    plt.savefig(filepath)
    print(f"📈 图表已保存到：{filepath}")

    plt.close()
