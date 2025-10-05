import json
import os

class BasicRiskManager:
    def __init__(self, max_risk_per_trade=0.02, max_position_size=1, stop_loss_pct=0.03, take_profit_pct=0.05, entry_file="entry_price.json"):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.entry_file = entry_file
        self.entry_price = self.load_entry_price()

    def load_entry_price(self):
        if os.path.exists(self.entry_file):
            try:
                with open(self.entry_file, "r") as f:
                    return json.load(f)  # 返回整个 dict
            except:
                return {}
        return {}

    def save_entry_price(self, price):
        with open(self.entry_file, "w") as f:
            json.dump(price, f)

    def record_entry_price(self, symbol, price):
        self.entry_price[symbol] = price  # 存每个 symbol 的入场价
        self.save_entry_price(self.entry_price)  # 保存整个 dict
        print(f"✅ 已记录 {symbol} 买入价格：{price}")

    def clear_entry_price(self, symbol):
        if symbol in self.entry_price:
            self.entry_price.pop(symbol)
            self.save_entry_price(self.entry_price)
            print(f"🗑️ 已清除 {symbol} 的 entry_price")

    def allow_entry(self, broker, current_price):
        positions = broker.get_all_positions()
        if len(positions) >= self.max_position_size:
            print(f"⚠️ 已达到最大仓位限制 ({len(positions)})，禁止继续加仓")
            return False
        return True

    def should_stop_loss(self, symbol, current_price):
        entry = self.entry_price.get(symbol)
        if entry is None:
            return False
        loss_pct = (entry - current_price) / entry
        print(f"🔻 {symbol} 当前浮动亏损: {loss_pct:.2%}")
        return loss_pct >= self.stop_loss_pct

    def should_take_profit(self, symbol, current_price):
        entry = self.entry_price.get(symbol)
        if entry is None:
            return False
        profit_pct = (current_price - entry) / entry
        print(f"📈 {symbol} 当前浮动盈利: {profit_pct:.2%}")
        return profit_pct >= self.take_profit_pct

    def get_entry_price(self, symbol):
        return self.entry_price.get(symbol)
