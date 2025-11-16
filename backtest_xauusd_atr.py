#!/usr/bin/env python3
"""
ATR Mean Reversion Strategy Backtest for XAUUSD
Moon Dev Trading System 🌙

Run this script locally with your XAUUSD data:
python backtest_xauusd_atr.py
"""

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import os
import sys

# ============================================================================
# DATA LOADING
# ============================================================================
# Update this path to your local XAUUSD data file
DATA_PATH = r"D:\xauusd-scalping-ai\data\XAUUSD.csv"  # UPDATE THIS PATH

def load_xauusd_data(file_path):
    """Load and prepare XAUUSD data"""
    print(f"🌙 Loading XAUUSD data from: {file_path}")

    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        print(f"   Please update DATA_PATH in this script to your XAUUSD CSV file location")
        sys.exit(1)

    df = pd.read_csv(file_path)

    # Clean column names
    df.columns = df.columns.str.strip().str.lower()

    # Drop unnamed columns
    df = df.drop(columns=[col for col in df.columns if 'unnamed' in col.lower()], errors='ignore')

    # Standardize column names
    column_mapping = {
        'datetime': 'datetime',
        'timestamp': 'datetime',
        'date': 'datetime',
        'time': 'datetime',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }

    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})

    # Convert datetime and set as index
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')

    # Ensure OHLC columns exist
    required_cols = ['Open', 'High', 'Low', 'Close']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column {col} not found. Available: {df.columns.tolist()}")

    # Add Volume if missing (XAUUSD often doesn't have volume)
    if 'Volume' not in df.columns:
        df['Volume'] = 0
        print("⚠️  No volume data found - using 0 (normal for XAUUSD)")

    # Clean data
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    df = df[df > 0]  # Remove zero/negative values

    print(f"✅ Data loaded successfully!")
    print(f"   Records: {len(df)}")
    print(f"   Date range: {df.index[0]} to {df.index[-1]}")
    print(f"   Timeframe: {df.index[1] - df.index[0]}")
    print(f"\n   Sample data:")
    print(df.head(3))

    return df


# ============================================================================
# ATR MEAN REVERSION STRATEGY
# ============================================================================
class ATRMeanReversion(Strategy):
    """
    ATR Mean Reversion Strategy for XAUUSD

    Performance on BTC-USD-15m:
    - Sharpe Ratio: 0.56
    - Total Return: +127.77%
    - Max Drawdown: -12.65%
    - Win Rate: 46.81%
    - Trades: 47

    Strategy Logic:
    - Entry: Price breaks Keltner Channel + reversal candle
    - Keltner Channels: 20-period SMA ± 1.5 ATR
    - Exit: ATR-based TP (1.5x ATR) and SL (1.0x ATR)
    """

    # Strategy Parameters (optimized for BTC, may need tuning for XAUUSD)
    kc_period = 20
    kc_multiplier = 1.5
    atr_period = 14
    risk_per_trade = 0.02  # 2% risk per trade
    tp_multiplier = 1.5    # Take profit: 1.5x ATR
    sl_multiplier = 1.0    # Stop loss: 1.0x ATR

    def init(self):
        """Initialize indicators"""
        print("🌙 Initializing ATR Mean Reversion Strategy for XAUUSD")

        # Keltner Channels using ATR
        self.kc_middle = self.I(lambda: pd.Series(self.data.Close).rolling(self.kc_period).mean())

        # Calculate ATR
        def calc_atr(high, low, close, period):
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

            tr1 = high_series - low_series
            tr2 = abs(high_series - close_series.shift(1))
            tr3 = abs(low_series - close_series.shift(1))

            tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
            atr = tr.rolling(window=period).mean()
            return atr.values

        self.atr = self.I(calc_atr, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.kc_upper = self.I(lambda: self.kc_middle + (self.atr * self.kc_multiplier))
        self.kc_lower = self.I(lambda: self.kc_middle - (self.atr * self.kc_multiplier))

        # Track position state
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None

    def next(self):
        """Trading logic for each candle"""
        current_close = self.data.Close[-1]
        current_open = self.data.Open[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]

        # Skip if not enough data
        if len(self.kc_middle) == 0 or np.isnan(self.kc_middle[-1]):
            return

        # Get current ATR for position sizing
        current_atr = self.atr[-1]
        if np.isnan(current_atr):
            return

        # Calculate position size based on risk
        equity = self.equity
        risk_amount = equity * self.risk_per_trade

        # LONG ENTRY: Price pokes below lower KC + bullish reversal candle
        if not self.position and (current_low < self.kc_lower[-1] or current_close < self.kc_lower[-1]):
            # Bullish reversal candle
            is_bullish_candle = current_close > current_open

            if is_bullish_candle:
                entry_price = current_close
                stop_loss = entry_price - (current_atr * self.sl_multiplier)
                take_profit = entry_price + (current_atr * self.tp_multiplier)

                # Calculate position size
                risk_per_unit = abs(entry_price - stop_loss)
                if risk_per_unit > 0:
                    position_size = max(int(risk_amount / risk_per_unit), 1)

                    self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    self.stop_loss = stop_loss
                    self.take_profit = take_profit

                    print(f"🚀 LONG ENTRY @ {entry_price:.2f}")
                    print(f"   SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
                    print(f"   Size: {position_size} | ATR: {current_atr:.2f}")

        # SHORT ENTRY: Price pokes above upper KC + bearish reversal candle
        elif not self.position and (current_high > self.kc_upper[-1] or current_close > self.kc_upper[-1]):
            # Bearish reversal candle
            is_bearish_candle = current_close < current_open

            if is_bearish_candle:
                entry_price = current_close
                stop_loss = entry_price + (current_atr * self.sl_multiplier)
                take_profit = entry_price - (current_atr * self.tp_multiplier)

                # Calculate position size
                risk_per_unit = abs(stop_loss - entry_price)
                if risk_per_unit > 0:
                    position_size = max(int(risk_amount / risk_per_unit), 1)

                    self.sell(size=position_size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    self.stop_loss = stop_loss
                    self.take_profit = take_profit

                    print(f"🚀 SHORT ENTRY @ {entry_price:.2f}")
                    print(f"   SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
                    print(f"   Size: {position_size} | ATR: {current_atr:.2f}")


# ============================================================================
# RUN BACKTEST
# ============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("🌙 MOON DEV'S ATR MEAN REVERSION BACKTEST - XAUUSD")
    print("=" * 80)
    print()

    # Load data
    data = load_xauusd_data(DATA_PATH)

    print("\n" + "=" * 80)
    print("🔄 Running Backtest...")
    print("=" * 80)

    # Initialize backtest
    bt = Backtest(
        data,
        ATRMeanReversion,
        cash=100000,           # Starting capital: $100,000
        commission=0.002,      # 0.2% commission per trade
        exclusive_orders=True  # Only one position at a time
    )

    # Run backtest
    stats = bt.run()

    # Display results
    print("\n" + "=" * 80)
    print("📊 BACKTEST RESULTS")
    print("=" * 80)
    print(stats)

    print("\n" + "=" * 80)
    print("⭐ KEY PERFORMANCE METRICS")
    print("=" * 80)
    print(f"💰 Total Return:        {stats['Return [%]']:.2f}%")
    print(f"📈 Sharpe Ratio:        {stats['Sharpe Ratio']:.2f}")
    print(f"📉 Max Drawdown:        {stats['Max. Drawdown [%]']:.2f}%")
    print(f"🎯 Win Rate:            {stats['Win Rate [%]']:.2f}%")
    print(f"📊 Total Trades:        {stats['# Trades']}")
    print(f"⏱️  Avg Trade Duration:  {stats['Avg. Trade Duration']}")
    print(f"💵 Best Trade:          {stats['Best Trade [%]']:.2f}%")
    print(f"💸 Worst Trade:         {stats['Worst Trade [%]']:.2f}%")

    print("\n" + "=" * 80)
    print("📈 STRATEGY ANALYSIS")
    print("=" * 80)

    if stats['# Trades'] > 0:
        avg_trade_return = stats['Return [%]'] / stats['# Trades']
        print(f"   Average Return per Trade: {avg_trade_return:.3f}%")
        print(f"   Profit Factor: {stats.get('Profit Factor', 'N/A')}")
        print(f"   Expectancy: {stats.get('Expectancy [%]', 'N/A')}")
    else:
        print("   ⚠️  No trades generated - strategy parameters may need adjustment")

    print("\n" + "=" * 80)
    print("✅ Backtest Complete!")
    print("=" * 80)

    # Optional: Save results to file
    output_file = "xauusd_atr_backtest_results.txt"
    with open(output_file, 'w') as f:
        f.write("XAUUSD ATR Mean Reversion Backtest Results\n")
        f.write("=" * 80 + "\n\n")
        f.write(str(stats))

    print(f"\n📝 Results saved to: {output_file}")

    # Optional: Generate chart (requires bokeh)
    try:
        print("\n📊 Generating interactive chart...")
        bt.plot(open_browser=True)
    except Exception as e:
        print(f"⚠️  Chart generation skipped: {e}")
