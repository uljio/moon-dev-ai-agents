# 🌙 XAUUSD ATR Mean Reversion Backtest Instructions

## Quick Start

### Option 1: Run Locally on Your Machine (Recommended)

1. **Update the data path** in `backtest_xauusd_atr.py`:
   ```python
   DATA_PATH = r"D:\xauusd-scalping-ai\data\XAUUSD.csv"  # Update this line
   ```

2. **Ensure you have required packages**:
   ```bash
   pip install pandas numpy backtesting bokeh
   ```

3. **Run the backtest**:
   ```bash
   python backtest_xauusd_atr.py
   ```

4. **View results**:
   - Console will show detailed statistics
   - `xauusd_atr_backtest_results.txt` will be created
   - Interactive chart will open in your browser

---

### Option 2: Upload Data to Repository

If you want me to run the backtest:

1. Copy your XAUUSD CSV file to:
   ```
   /home/user/moon-dev-ai-agents/src/data/XAUUSD-15m.csv
   ```

2. Your CSV should have this format:
   ```csv
   datetime,open,high,low,close,volume
   2023-01-01 00:00:00,1824.50,1825.30,1823.20,1824.80,0
   2023-01-01 00:15:00,1824.80,1826.10,1824.50,1825.90,0
   ```
   (Volume can be 0 for XAUUSD)

3. Let me know and I'll run the backtest immediately

---

## Strategy Details

### ATR Mean Reversion Strategy

**Entry Rules:**
- **Long**: Price pokes below lower Keltner Channel + bullish reversal candle (close > open)
- **Short**: Price pokes above upper Keltner Channel + bearish reversal candle (close < open)

**Keltner Channels:**
- Middle: 20-period SMA
- Upper/Lower: Middle ± (1.5 × ATR)

**Exit Rules:**
- Take Profit: Entry ± 1.5 × ATR
- Stop Loss: Entry ± 1.0 × ATR

**Risk Management:**
- 2% risk per trade
- Position size calculated based on stop loss distance
- Only one position at a time

---

## Expected Performance (Based on BTC-USD-15m)

| Metric | Value |
|--------|-------|
| Sharpe Ratio | 0.56 |
| Total Return | +127.77% |
| Max Drawdown | -12.65% |
| Win Rate | 46.81% |
| Total Trades | 47 |

**Note**: XAUUSD performance may differ due to different volatility characteristics.

---

## Optimizing for XAUUSD

If you get too few trades, adjust these parameters in the script:

```python
class ATRMeanReversion(Strategy):
    kc_period = 20          # Try 10-30
    kc_multiplier = 1.5     # Try 1.0-2.5 (lower = more trades)
    atr_period = 14         # Try 10-20
    risk_per_trade = 0.02   # 2% risk
    tp_multiplier = 1.5     # Try 1.0-3.0
    sl_multiplier = 1.0     # Try 0.5-2.0
```

**Tips:**
- **Lower kc_multiplier** (e.g., 1.0) = more trades
- **Higher kc_multiplier** (e.g., 2.5) = fewer, higher quality trades
- XAUUSD is more volatile than BTC, so consider:
  - kc_multiplier = 1.2-1.8 (wider channels for volatility)
  - tp_multiplier = 2.0-3.0 (larger profit targets)

---

## Troubleshooting

### No Trades Generated?
- **Too restrictive parameters**: Lower `kc_multiplier` to 1.0
- **Wrong timeframe**: Works best on 15m-4H timeframes
- **Insufficient data**: Need at least 20 candles for indicators

### Poor Performance?
- **Optimize parameters**: Run parameter optimization (see below)
- **Wrong timeframe**: Try different timeframes (1H or 4H often better for XAUUSD)
- **Market regime**: Strategy works best in ranging/mean-reverting markets

### Parameter Optimization

Add this to the end of `backtest_xauusd_atr.py`:

```python
# Optimize strategy parameters
stats_optimized = bt.optimize(
    kc_multiplier=range(10, 25, 5) / 10,  # 1.0, 1.5, 2.0
    tp_multiplier=range(10, 30, 5) / 10,  # 1.0, 1.5, 2.0, 2.5
    maximize='Sharpe Ratio',
    constraint=lambda p: p['# Trades'] > 10
)
print("\n🎯 Optimized Parameters:")
print(stats_optimized)
```

---

## Questions?

Just let me know if you need help:
1. Running the backtest
2. Optimizing parameters
3. Interpreting results
4. Modifying the strategy for XAUUSD
