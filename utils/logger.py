import os
import datetime

def log_trade(action, symbol, price, reason="", broker=None, log_dir="logs", keep_days=15):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")

    # 构建账户信息（可选）
    equity_str = ""
    if broker:
        try:
            account = broker.get_account()
            cash = float(account.cash)
            equity = float(account.equity)
            position_value = equity - cash
            equity_str = f"｜现金: ${cash:.2f}, 持仓: ${position_value:.2f}, 总权益: ${equity:.2f}"
        except Exception as e:
            equity_str = f"｜账户信息获取失败: {e}"

    # 日志内容
    log_entry = f"[{timestamp}] {action} {symbol} @ {price:.2f} - {reason} {equity_str}\n"

    # 创建 logs 目录
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{date_str}.txt")

    # 写入日志文件
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)

    # 同步输出到控制台
    print("📘 日志记录:", log_entry.strip())

    # 清理旧日志
    clean_old_logs(log_dir, keep_days)

def log_pnl(entry_price, current_price, symbol, log_dir="logs"):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")

    pnl = (current_price - entry_price) / entry_price
    direction = "浮盈" if pnl >= 0 else "浮亏"
    message = f"📊 持仓中，入场价: {entry_price:.2f}, 当前价: {current_price:.2f}, {direction}: {pnl:.2%}"
    log_entry = f"[{timestamp}] {message}\n"

    # 确保目录存在
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{date_str}.txt")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)

    print(log_entry.strip())
    print(f"✅ 已调用 log_pnl()，entry: {entry_price}, price: {current_price}")

def clean_old_logs(log_dir="logs", keep_days=15):
    now = datetime.datetime.now()
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            try:
                file_date_str = filename.replace(".txt", "")
                file_date = datetime.datetime.strptime(file_date_str, "%Y-%m-%d")
                age = (now - file_date).days
                if age > keep_days:
                    os.remove(file_path)
                    print(f"🗑️ 已自动清除旧日志：{filename}（{age} 天前）")
            except:
                continue
