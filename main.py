import os
from utils.logger import log_pnl

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
import time
from datetime import datetime

from utils.notifier import send_notification

# 1. 初始化交易客户端（用于下单）
trading_client = TradingClient(API_KEY, API_SECRET, paper=True)

# 2. 初始化数据客户端（用于获取价格）
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

# 3. 初始化策略（根据你需要可以切换）
# strategy = SMAStrategy(API_KEY, API_SECRET)
strategy = RSIStrategy(API_KEY, API_SECRET)
#strategy = HybridStrategy(API_KEY, API_SECRET)

# 4. 初始化风控
risk = BasicRiskManager(max_position_size=10)

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
    send_notification("🟢 已下单 BUY", f"{symbol} @ {get_current_price(symbol):.2f}")


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
    send_notification("🔴 已下单 SELL", f"{symbol} @ {get_current_price(symbol):.2f}")




# 8. 主逻辑
def main():
    #backtest_and_plot("AAPL", days=90)
    clean_old_logs()
    #每轮同步持仓与entry_price，避免旧记录
    sync_entry_prices()
    for symbol in SYMBOLS:
        print(f"\n🔁 处理标的：{symbol}")
    # 获取当前价格
        request_params = StockLatestTradeRequest(symbol_or_symbols=[symbol])
        response = data_client.get_stock_latest_trade(request_params)
        current_price = response[symbol].price

        backtest_and_plot(symbol, days=90)


    # 获取信号
        signal = strategy.get_signal(symbol)
        #signal = "SELL"
    #signal = "BUY"
        print("🧪 是否持仓中:", has_position(symbol))
        print("📦 entry_price = ", risk.get_entry_price(symbol))
    # 执行逻辑
        if signal == "BUY" and not has_position(symbol) and risk.allow_entry(trading_client, current_price):
            print("✅ 进入下单逻辑")
            buy(symbol)
            risk.record_entry_price(symbol, current_price)
        elif has_position(symbol):
            entry_price = risk.get_entry_price(symbol)  # ✅ 统一提前获取
            if risk.should_stop_loss(symbol, current_price):
                print("⚠️ 持仓中，止损触发卖出")
                send_notification("⚠️ 持仓中，止损触发卖出", f"{symbol} @ {current_price:.2f}")
                sell(symbol)
                risk.clear_entry_price(symbol)
            elif risk.should_take_profit(symbol,current_price):
                print("🎯 持仓中，止盈触发卖出")
                send_notification("🎯 持仓中，止盈触发卖出", f"{symbol} @ {current_price:.2f}")
                sell(symbol)
                risk.clear_entry_price(symbol)
            elif signal == "SELL":
                sell(symbol)
                risk.clear_entry_price(symbol)
            # ✅ 新增：当日盈利达到阈值（如 1%）时也止盈
            elif risk.should_take_intraday_profit(entry_price, current_price, threshold=1.0):
                print("💰 当日浮盈已达阈值，立即卖出止盈")
                send_notification("💰 浮盈止盈", f"{symbol} 盈利超 {1.0:.2f}%，卖出止盈")
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
                entry_price = risk.get_entry_price(symbol)
                if entry_price:
                    price = current_price
                    pnl = (price - entry_price) / entry_price * 100
                    direction = "浮盈" if pnl >= 0 else "浮亏"
                    print(f"📊 持仓中，入场价: {entry_price:.2f}，现价: {price:.2f}，{direction}: {pnl:.2f}%")
                    log_pnl(entry_price, price, symbol)
            else:
                print("⏳ 无操作")
                #send_notification("没有触发策略条件，因此无操作", f"{symbol} @ {get_current_price(symbol):.2f}")
def generate_eod_report():


    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    log_path = os.path.join("logs", f"{today_str}.txt")

    report = f"📊【每日收盘报告 - {today_str}】\n\n"

    # 1. 汇总持仓盈亏
    report += "📦 当前持仓盈亏情况：\n"
    positions = trading_client.get_all_positions()
    if positions:
        for p in positions:
            entry = float(p.avg_entry_price)
            qty = float(p.qty)
            current = float(p.current_price)
            change_pct = (current - entry) / entry * 100
            symbol = p.symbol
            report += f"- {symbol}: {qty}股，入场价 {entry:.2f}，现价 {current:.2f}，盈亏 {change_pct:.2f}%\n"
    else:
        report += "- 当前无持仓\n"

    # 2. 今日交易日志概要
    report += "\n📝 今日交易操作：\n"
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        today_logs = [line for line in lines if "BUY" in line or "SELL" in line]
        if today_logs:
            report += "".join(today_logs[-5:])  # 最多展示5条
        else:
            report += "- 今日无买卖操作\n"
    else:
        report += "- 日志文件不存在\n"

    # 3. 明日信号预测（RSI）
    report += "\n🔮 明日预测信号（RSI策略）:\n"
    rsi = RSIStrategy(API_KEY, API_SECRET)
    for sym in SYMBOLS:
        try:
            signal = rsi.get_signal(sym)
            report += f"- {sym}: {signal}\n"
        except Exception as e:
            report += f"- {sym}: 获取失败（{e}）\n"

    # 4. 通过 Telegram 发送报告
    send_notification("📊 每日收盘报告", report)



def is_market_open():
    now = datetime.now()
    return now.weekday() < 5 and now.hour >= 9 and now.hour < 16
    #return True

def run_bot_loop():
    print("⏳ 等待开盘时间 9:30 AM 开始运行")
    while True:
        now = datetime.now()
        # 每天只在交易时间运行
        if now.hour == 16 and now.minute == 0:
            print("📈 收盘时间到，今天交易结束。正在生成报告...")
            generate_eod_report()
            break

        if is_market_open():
            print(f"\n🕒 当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}，执行策略检查")
            try:
                main()
            except Exception as e:
                print(f"⚠️ 出现错误：{e}")
            time.sleep(30)
        else:
            print(f"⏳ 交易时间未到（当前 {now.strftime('%H:%M')}），等待中...")
            time.sleep(60)

def sync_entry_prices():
    """自动清理没有持仓但还留在entry_price里的记录"""
    current_positions = trading_client.get_all_positions()
    current_symbols = [p.symbol.upper() for p in current_positions]

    for sym in list(risk.entry_price.keys()):
        if sym.upper() not in current_symbols:  # 如果本地有但账户没有
            risk.clear_entry_price(sym)  # 自动清除

if __name__ == "__main__":
    run_bot_loop()
