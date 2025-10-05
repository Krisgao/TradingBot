class PaperBroker:
    def __init__(self, starting_cash):
        self.cash = starting_cash
        self.positions = {}  # 保存当前持仓价格

    def buy(self, symbol, price):
        if symbol not in self.positions:
            self.positions[symbol] = price
            print(f"✅ BUY {symbol} at {price}")
        else:
            print(f"⚠️ 已持有 {symbol}，不能重复买入")

    def sell(self, symbol, price):
        if symbol in self.positions:
            entry = self.positions[symbol]
            pnl = price - entry
            self.cash += pnl
            print(f"💰 SELL {symbol} at {price}, PnL: {pnl:.2f}")
            del self.positions[symbol]
        else:
            print(f"⚠️ 没有持有 {symbol}，无法卖出")

    def has_position(self, symbol):
        return symbol in self.positions

    def get_entry_price(self, symbol):
        return self.positions.get(symbol)

    def get_portfolio_value(self, price_map):
        total = self.cash
        for symbol, entry in self.positions.items():
            current_price = price_map.get(symbol, entry)
            total += current_price
        return total

