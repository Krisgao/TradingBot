# 🦾 TradingBot | 多资产智能交易机器人

🚀 A smart multi-asset trading bot powered by Python, built for live trading and backtesting.  
🚀 一个由 Python 构建的智能多标的交易机器人，支持实盘交易与回测。

---

## 📌 Features | 功能亮点

- 📈 **Strategy-Based Framework**  
  Modular architecture to easily plug in different trading strategies.  
  模块化架构，支持快速接入不同的交易策略。

- ⏱️ **Real-Time Data Streaming**  
  Ready for integration with live market data APIs (e.g., Alpaca).  
  支持实时数据流处理，兼容市面主流交易 API（如 Alpaca）。

- 🧪 **Backtesting System**  
  Run historical backtests and visualize trading performance.  
  历史回测系统，帮助评估策略优劣与回报情况。

- 📊 **Risk Management**  
  Customizable stop-loss, take-profit, position sizing, etc.  
  内建风控功能：止盈止损、仓位控制等可自由配置。

- 🧠 **Strategy Switching Ready**  
  Clean separation of strategy logic and execution logic.  
  策略逻辑与执行逻辑分离，方便灵活切换策略。

---

## 🗂️ Project Structure | 项目结构

```
TradingBot/
├── backtest/          # 回测模块
├── broker/            # 经纪商 API 封装（如 Alpaca）
├── data/              # 数据加载模块
├── risk/              # 风控策略配置
├── strategies/        # 各类交易策略
├── utils/             # 工具函数
├── .gitignore         # 忽略配置
└── main.py            # 主程序入口
```

---

## 🚀 Quick Start | 快速开始

### ✅ Clone the repo | 克隆项目

```bash
git clone https://github.com/Krisgao/TradingBot.git
cd TradingBot
```

### ⚙️ Install dependencies | 安装依赖

```bash
pip install alpaca-trade-api pandas numpy ta matplotlib requests python-dotenv
```

### 🧪 Backtest a strategy | 回测策略示例

```bash
python main.py --mode backtest --strategy sma
```

### 🔴 Live trading (Paper mode) | 启动实盘（纸上测试）

> ⚠️ 请确保在 `config.py` 中配置好你的交易 API 密钥

```bash
python main.py --mode live --strategy hybrid
```

---

## 📉 Built-in Strategies | 内置策略

| 策略文件 | 描述 |
|----------|------|
| `sma_strategy.py` | 双均线策略 |
| `rsi_strategy.py` | RSI 超买超卖 |
| `hybrid_strategy.py` | 混合型策略（SMA+RSI）|

你也可以自定义策略，只需继承 `BaseStrategy` 并实现 `generate_signals()` 方法。

---

## 🛡️ Disclaimer | 免责声明

This project is for **educational and research purposes only**.  
本项目仅供学习与研究使用，**请勿直接用于实盘交易，风险自负。**

---

## ⭐ Star this repo | 点个 Star 吧！

如果你觉得这个项目有用，欢迎点个 Star ⭐ 支持我继续更新！  
If this repo helps you, feel free to star it and follow for more updates.

---

## 🙋‍♂️ Author | 作者

**Kris Gao**  
🧠 Passionate about algorithmic trading, backend engineering, and AI.  
📫 [GitHub](https://github.com/Krisgao)

---
