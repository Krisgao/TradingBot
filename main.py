from strategies.sma_strategy import SMAStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.hybrid_strategy import HybridStrategy

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from config import API_KEY, API_SECRET, BASE_URL
from risk.basic_risk import BasicRiskManager
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from backtest.plot import backtest_and_plot
from utils.logger import log_trade, clean_old_logs, log_pnl

# 1. 初始化交易客户端（用于下单）
trading_client = TradingClient(API_KEY, API_SECRET, paper=True)

# 2. 初始化数据客户端（用于获取价格）
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

# 3. 初始化策略（根据你需要可以切换）
# strategy = SMAStrategy(API_KEY, API_SECRET)
# strategy = RSIStrategy(API_KEY, API_SECRET)
strategy = HybridStrategy(API_KEY, API_SECRET)

# 4. 初始化风控
risk = BasicRiskManager(max_position_size=1)

def load_symbols(file_path="symbol/symbols.txt"):
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        symbols = [line.strip().upper() for line in lines if line.strip()]
        print(f"✅ 已加载标的列表：{symbols}")
        return symbols
    except FileNotFoundError:
        print("❌ 找不到 symbol/symbols.txt，默认使用空列表")
        return []

SYMBOLS = load_symbols()



# 5. 判断是否已有持仓
def has_position(symbol):
    #return True
    positions = trading_client.get_all_positions()
    print("📋 当前所有持仓：")
    for p in positions:
        print(f"➡️ {p.symbol} x {p.qty} @ {p.avg_entry_price}")
        if p.symbol.upper() == symbol.upper():
            return True
    return False

# 获取当前价格
def get_current_price(symbol):
    request_params = StockLatestTradeRequest(symbol_or_symbols=[symbol])
    response = data_client.get_stock_latest_trade(request_params)
    return response[symbol].price


# 6. 买入
def buy(symbol):
    order = MarketOrderRequest(
        symbol=symbol,
        qty=1,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    #trading_client.submit_order(order)
    order_response = trading_client.submit_order(order)
    print("📤 订单提交响应：", order_response)
    print("✅ 已下单 BUY")
    log_trade("BUY", symbol, get_current_price(symbol), reason="策略信号 + 风控通过", broker=trading_client)


# 7. 卖出
def sell(symbol):
    order = MarketOrderRequest(
        symbol=symbol,
        qty=1,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order)
    print("✅ 已下单 SELL")
    log_trade("SELL", symbol, get_current_price(symbol), reason="卖出信号或风控触发", broker=trading_client)




# 8. 主逻辑
def main():
    backtest_and_plot("AAPL", days=90)
    clean_old_logs()
    for symbol in SYMBOLS:
        print(f"\n🔁 处理标的：{symbol}")
    # 获取当前价格
        request_params = StockLatestTradeRequest(symbol_or_symbols=[symbol])
        response = data_client.get_stock_latest_trade(request_params)
        current_price = response[symbol].price

    # 获取信号
        signal = strategy.get_signal(symbol)
        #signal = "BUY"
    #signal = "BUY"
        print("🧪 是否持仓中:", has_position(symbol))
        print("📦 entry_price = ", risk.get_entry_price(symbol))
    # 执行逻辑
        if signal == "BUY" and not has_position(symbol) and risk.allow_entry(trading_client, current_price):
            print("✅ 进入下单逻辑")
            buy(symbol)
            risk.record_entry_price(symbol, current_price)
        elif has_position(symbol):
            if risk.should_stop_loss(symbol, current_price):
                print("⚠️ 持仓中，止损触发卖出")
                sell(symbol)
                risk.clear_entry_price(symbol)
            elif risk.should_take_profit(current_price):
                print("🎯 持仓中，止盈触发卖出")
                sell(symbol)
                risk.clear_entry_price(symbol)
            elif signal == "SELL":
                sell(symbol)
                risk.clear_entry_price(symbol)
            else:
                print("📈 持仓中，无止损无止盈无卖出")
                entry_price = risk.get_entry_price(symbol)
                if entry_price:
                    pnl = (current_price - entry_price) / entry_price * 100
                    direction = "浮盈" if pnl >= 0 else "浮亏"
                    print(f"📊 持仓中，入场价: {entry_price:.2f}，现价: {current_price:.2f}，{direction}: {pnl:.2f}%")
                    log_pnl(entry_price, current_price, symbol)
        else:
            if has_position(symbol):
                entry_price = risk.get_entry_price()
                if entry_price:
                    price = current_price
                    pnl = (price - entry_price) / entry_price * 100
                    direction = "浮盈" if pnl >= 0 else "浮亏"
                    print(f"📊 持仓中，入场价: {entry_price:.2f}，现价: {price:.2f}，{direction}: {pnl:.2f}%")
                    log_pnl(entry_price, price, symbol)
            else:
                print("⏳ 无操作")


if __name__ == "__main__":
    main()
