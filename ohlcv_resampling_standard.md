# Standard OHLCV Resampling and Gap-Filling Design Pattern

When trading illiquid contracts, newly rolled expiries, or during low-volume periods, financial APIs (such as Breeze) often return **sparse data**—they only return 1-minute candles for minutes in which at least one trade occurred. If no trades occurred during a specific minute, that minute is entirely omitted.

Directly resampling this sparse data to higher timeframes (e.g., 3-min, 5-min, 10-min) causes resampled candles to have missing constituent minutes. If a bot strictly filters out incomplete candles (e.g., expecting exactly 10 minutes of data for a 10-minute candle), it will **discard entire candles**, leading to delayed or missing indicators and signals.

This document outlines the **world-standard design pattern** to resolve this by filling gaps in the 1-minute data before resampling.

---

## 1. Industry Standard Practice

In professional trading systems (e.g., Backtrader's `DataFiller`, Databento, Pandas-TA):
1. **Price Persistence:** The price of an asset does not disappear when there is no trading activity; it remains at the last traded price. Therefore, the last known `Close` price is **forward-filled** (`ffill()`).
2. **No Price Discovery:** During minutes with no trades, the `Open`, `High`, and `Low` are set equal to the forward-filled `Close` price (since there was no price movement).
3. **Volume:** The `Volume` is set to `0` (since zero contracts changed hands).

---

## 2. Generic Implementation Template (Pandas)

This reusable Python function cleans the raw 1-minute data, fills gaps using the forward-fill standard, resamples it to any target timeframe (1m, 3m, 5m, 10m, 15m, etc.), and filters out the final incomplete live candle.

```python
import pandas as pd
import numpy as np

def resample_ohlcv_with_fill(df: pd.DataFrame, interval_min: int) -> pd.DataFrame:
    """
    Standard Resampler for OHLCV financial data.
    
    1. Fills intraday gaps in 1-minute data using last traded price (forward-fill).
    2. Sets volume to 0 for missing periods.
    3. Resamples to target timeframe (interval_min).
    4. Drops the incomplete live boundary candle.
    """
    if df is None or df.empty or 'datetime' not in df.columns:
        return pd.DataFrame()
        
    work_df = df.copy()
    interval_min = max(1, int(interval_min))
    
    # Clean up datetime index
    work_df['datetime'] = pd.to_datetime(work_df['datetime'], errors='coerce')
    work_df.dropna(subset=['datetime'], inplace=True)
    work_df.set_index('datetime', inplace=True)
    work_df.sort_index(inplace=True)
    
    # Ensure numeric columns
    numeric_cols = ['open', 'high', 'low', 'close']
    if 'volume' in work_df.columns:
        numeric_cols.append('volume')
    for col in numeric_cols:
        work_df[col] = pd.to_numeric(work_df[col], errors='coerce')
    work_df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
    
    if work_df.empty:
        return pd.DataFrame()
        
    # --- STEP 1: Create a continuous 1-minute grid ---
    # Creates an entry for every single minute from start to end
    full_range = pd.date_range(start=work_df.index.min(), end=work_df.index.max(), freq='1min')
    work_df = work_df.reindex(full_range)
    
    # --- STEP 2: Forward Fill Prices and zero-fill Volume ---
    work_df['close'] = work_df['close'].ffill()
    work_df['open'] = work_df['open'].fillna(work_df['close'])
    work_df['high'] = work_df['high'].fillna(work_df['close'])
    work_df['low'] = work_df['low'].fillna(work_df['close'])
    if 'volume' in work_df.columns:
        work_df['volume'] = work_df['volume'].fillna(0)
        
    # --- STEP 3: Define Aggregation Rules ---
    agg_rules = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    }
    if 'volume' in work_df.columns:
        agg_rules['volume'] = 'sum'
        
    # --- STEP 4: Resample & Count Constituent Minutes ---
    resampled = work_df.resample(f'{interval_min}min', label='left', closed='left').agg(agg_rules)
    resampled['bar_count'] = work_df['close'].resample(f'{interval_min}min', label='left', closed='left').count()
    
    resampled.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
    
    # --- STEP 5: Discard Incomplete Live Boundary Candle ---
    # E.g., if interval is 10 min, and the current live candle only has 3 minutes of data,
    # it is dropped until all 10 minutes are complete.
    resampled = resampled[resampled['bar_count'] >= interval_min].copy()
    
    return resampled.reset_index().rename(columns={'index': 'datetime'})
```

---

## 3. Practical Example: 10-Minute Resampling

Let's resample a 10-minute block from **10:00 to 10:10** where a gap occurred at **10:05** (no trades):

### A. Raw Sparse Data (From Broker)
| datetime | open | high | low | close | volume |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 10:00:00 | 100.0 | 102.0 | 100.0 | 101.5 | 100 |
| 10:01:00 | 101.5 | 101.5 | 99.5  | 100.0 | 50 |
| 10:02:00 | 100.0 | 101.0 | 100.0 | 100.5 | 30 |
| 10:03:00 | 100.5 | 102.0 | 100.5 | 102.0 | 80 |
| 10:04:00 | 102.0 | 102.5 | 101.0 | 101.0 | 110 |
| **10:05:00** | *(Missing)* | *(Missing)* | *(Missing)* | *(Missing)* | *(Missing)* |
| 10:06:00 | 101.0 | 101.5 | 100.0 | 100.5 | 40 |
| 10:07:00 | 100.5 | 101.0 | 100.5 | 101.0 | 60 |
| 10:08:00 | 101.0 | 102.0 | 100.5 | 101.5 | 90 |
| 10:09:00 | 101.5 | 101.5 | 101.0 | 101.0 | 20 |

*Raw bar count = 9 (under the old logic, this entire candle would be deleted).*

### B. After Reindexing & Gap-Filling (Standard Practice)
| datetime | open | high | low | close | volume | Comment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 10:00:00 | 100.0 | 102.0 | 100.0 | 101.5 | 100 | |
| 10:01:00 | 101.5 | 101.5 | 99.5  | 100.0 | 50 | |
| 10:02:00 | 100.0 | 101.0 | 100.0 | 100.5 | 30 | |
| 10:03:00 | 100.5 | 102.0 | 100.5 | 102.0 | 80 | |
| 10:04:00 | 102.0 | 102.5 | 101.0 | 101.0 | 110 | |
| **10:05:00** | **101.0** | **101.0** | **101.0** | **101.0** | **0** | *Filled with 10:04 close* |
| 10:06:00 | 101.0 | 101.5 | 100.0 | 100.5 | 40 | |
| 10:07:00 | 100.5 | 101.0 | 100.5 | 101.0 | 60 | |
| 10:08:00 | 101.0 | 102.0 | 100.5 | 101.5 | 90 | |
| 10:09:00 | 101.5 | 101.5 | 101.0 | 101.0 | 20 | |

*Filled bar count = 10 (this candle will now be successfully kept).*

### C. Final Resampled Candle (10-minute)
* **Open:** 100.0 (from 10:00)
* **High:** 102.5 (from 10:04)
* **Low:** 99.5 (from 10:01)
* **Close:** 101.0 (from 10:09)
* **Volume:** 580 (Sum of all minutes)
* **Bar Count:** 10 (Kept successfully)

---

## 4. How to Integrate This Design Pattern

To implement this across all bots:
1. Locate the resampling function (often named `resample_complete_ohlcv` or similar) in the bot's signal or logic utility file.
2. Replace it with the `resample_ohlcv_with_fill` function from Section 2.
3. Keep the target timeframe (`interval_min`) dynamic to support any timeframe (e.g. `3`, `5`, `10`, `15` minutes).
