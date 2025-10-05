from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

import pandas as pd
import ta


class HybridStrategy:
    def __init__(self, api_key, api_secret):
        self.client = StockHistoricalDataClient(api_key, api_secret)

    def get_signal(self, symbol: str) -> str:
        # 1. 获取数据
        end = datetime.now()
        start = end - timedelta(days=30)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
        )

        bars = self.client.get_stock_bars(request).df

        if bars.empty or len(bars) < 15:
            print("❌ 数据不足")
            return "HOLD"

        closes = bars['close']

        # 2. 计算 SMA 和 RSI
        sma = closes.rolling(window=20).mean()
        rsi = ta.momentum.RSIIndicator(pd.Series(closes), window=14).rsi()

        latest_price = closes.iloc[-1]
        latest_sma = sma.iloc[-1]
        latest_rsi = rsi.iloc[-1]

        print(f"[混合策略] 当前价格: {latest_price:.2f}, SMA(20): {latest_sma:.2f}, RSI(14): {latest_rsi:.2f}")

        # 3. 策略逻辑：趋势向上 + RSI 超卖 = 买入；趋势向下 + RSI 超买 = 卖出
        if latest_price > latest_sma and latest_rsi < 30:
            return "BUY"
        elif latest_price < latest_sma and latest_rsi > 70:
            return "SELL"
        else:
            return "HOLD"
