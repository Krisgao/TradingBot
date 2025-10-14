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

def backtest_and_plot(symbol, days=90, save_dir="backtest", rsi_buy_thresh=30, rsi_sell_thresh=70):
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
        print(f"{df.loc[i, 'timestamp']}: price={price:.2f}, sma={sma:.2f}, rsi={rsi:.2f}")
        # 买入逻辑不变（RSI 超卖）
        if not position and rsi < rsi_buy_thresh:
            position = True
            buy_dates.append(df.loc[i, "timestamp"])
            buy_prices.append(price)

        # 卖出逻辑放宽，只看 RSI 超买
        elif position and rsi > rsi_sell_thresh:
            position = False
            sell_dates.append(df.loc[i, "timestamp"])
            sell_prices.append(price)

    #混合策略
        # if not position and price > sma and rsi < rsi_buy_thresh:
        #     position = True
        #     buy_dates.append(df.loc[i, "timestamp"])
        #     buy_prices.append(price)
        #
        # elif position and price < sma and rsi > rsi_sell_thresh:
        #     position = False
        #     sell_dates.append(df.loc[i, "timestamp"])
        #     sell_prices.append(price)

    # === 4. 胜率与收益统计 ===
    profits = []
    for buy, sell in zip(buy_prices, sell_prices):
        profits.append(sell - buy)

    total_trades = len(profits)
    win_trades = sum(p > 0 for p in profits)
    win_rate = win_trades / total_trades if total_trades > 0 else 0
    avg_profit = sum(profits) / total_trades if total_trades > 0 else 0

    # 输出结果
    print(f"📊 回测指标：")
    print(f"总交易次数: {total_trades}")
    print(f"胜率: {win_rate:.2%}")
    print(f"平均每笔收益: {avg_profit:.2f}")

    # 3. 绘图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

    # 价格图
    ax1.plot(df["timestamp"], df["close"], label="价格", color="blue")
    ax1.plot(df["timestamp"], df["sma"], label="SMA(20)", linestyle="--", color="gray")
    ax1.scatter(buy_dates, buy_prices, marker="^", color="green", label="BUY", s=100)
    ax1.scatter(sell_dates, sell_prices, marker="v", color="red", label="SELL", s=100)
    ax1.set_ylabel("价格")
    ax1.set_title(f"{symbol} 回测图表（Hybrid策略）")
    ax1.legend()
    ax1.grid(True)

    # RSI 图
    ax2.plot(df["timestamp"], df["rsi"], label="RSI(14)", color="purple")
    ax2.axhline(30, color="green", linestyle="--", label="RSI 30")
    ax2.axhline(70, color="red", linestyle="--", label="RSI 70")
    ax2.set_ylabel("RSI")
    ax2.set_xlabel("时间")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    filepath = f"{save_dir}/{symbol}_b{rsi_buy_thresh}_s{rsi_sell_thresh}.png"
    plt.savefig(filepath)
    print(f"📈 图表已保存到：{filepath}")
    plt.close()

    # plt.figure(figsize=(14, 6))
    # plt.plot(df["timestamp"], df["close"], label="价格", color="blue")
    # plt.plot(df["timestamp"], df["sma"], label="SMA(20)", linestyle="--", color="gray")
    # plt.scatter(buy_dates, buy_prices, marker="^", color="green", label="BUY", s=100)
    # plt.scatter(sell_dates, sell_prices, marker="v", color="red", label="SELL", s=100)
    #
    # plt.title(f"{symbol} 回测图表（Hybrid策略）")
    # plt.xlabel("时间")
    # plt.ylabel("价格")
    # plt.legend()
    # plt.grid(True)
    # plt.tight_layout()
    #
    # # 保存图像
    # os.makedirs(save_dir, exist_ok=True)
    # filepath = f"{save_dir}/{symbol}_backtest.png"
    # plt.savefig(filepath)
    # print(f"📈 图表已保存到：{filepath}")
    #
    # plt.close()

# if __name__ == "__main__":
#     SYMBOLS = ["AMD", "META", "NVDA", "SHOP","NFLX","MARA","RIOT"]
#     for symbol in SYMBOLS:
#         for buy in [25, 30, 35, 40]:
#             for sell in [60,65, 70, 75]:
#                 print(f"\n📊 股票: {symbol} | 回测参数: RSI买入<{buy}, 卖出>{sell}")
#                 backtest_and_plot(symbol, days=90, save_dir="backtest", rsi_buy_thresh=buy, rsi_sell_thresh=sell)