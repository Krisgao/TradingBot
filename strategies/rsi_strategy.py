from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

import pandas as pd
import ta


class RSIStrategy:
    def __init__(self, api_key, api_secret):
        self.client = StockHistoricalDataClient(api_key, api_secret)

    def get_signal(self, symbol: str) -> str:
        # 1. 获取最近20天的数据（计算RSI需要多一点数据）
        end = datetime.now()
        start = end - timedelta(days=30)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
        )

        bars = self.client.get_stock_bars(request).df

        # 2. 处理数据
        if bars.empty or len(bars) < 15:
            print(f"[RSI策略] ❌ 获取{symbol}数据失败或数据不足（共 {len(bars)} 条）")
            return "HOLD"

        closes = bars['close']
        rsi_series = ta.momentum.RSIIndicator(pd.Series(closes), window=14).rsi()

        latest_rsi = rsi_series.iloc[-1]
        latest_price = closes.iloc[-1]

        print(f"[RSI策略] 当前价格: {latest_price:.2f}, RSI(14): {latest_rsi:.2f}")

        # 3. 生成信号
        if latest_rsi < 40:
            return "BUY"
        elif latest_rsi > 60:
            return "SELL"
        else:
            return "HOLD"
