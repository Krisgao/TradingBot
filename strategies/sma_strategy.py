from alpaca.data.requests import StockBarsRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta


class SMAStrategy:
    def __init__(self, api_key, api_secret):
        self.client = StockHistoricalDataClient(api_key, api_secret)

    def get_signal(self, symbol: str) -> str:
        end = datetime.now()
        start = end - timedelta(days=20)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start,
            end=end
        )

        bars = self.client.get_stock_bars(request).df
        closes = bars['close'].tail(5)
        sma = closes.mean()
        latest = closes.iloc[-1]

        print(f"[SMA策略] 当前: {latest:.2f}, SMA(5): {sma:.2f}")

        if latest > sma:
            return "BUY"
        elif latest < sma:
            return "SELL"
        else:
            return "HOLD"