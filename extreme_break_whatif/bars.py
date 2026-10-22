"""Per-bar entry-gate state for nifty (SENSEX) and retire (NIFTY), rebuilt from clean data.

Each day is computed the way the bot computes it: its own lookback window, its own
resampler, its own indicators (functions pulled from the master source by livefuncs).
All indicators here are causal, so one pass over [lookback + day] gives the value the
bot saw at every bar's evaluation.
"""
import datetime as dt
import re

import pandas as pd
import pandas_ta as ta

import livefuncs as L

CLEAN = "/Users/vivek/Documents/nifty/data/clean.nosync"
NIFTY_LOOKBACK_DAYS = 10        # nifty_ema34_signal.calculate_latest_ema_bands
RETIRE_LOOKBACK_DAYS = 4        # retire_single_leg.fetch_nifty_resampled_data
INTERVAL_MIN = 10
NIFTY_MAX_DISTANCE = 1000.0     # ENTRY_BAND_MAX_DISTANCE (logs: "<= 1000.0")
NIFTY_ENTRY_CUTOFF = dt.time(15, 0)
RETIRE_LAST_ENTRY = dt.time(15, 18)
RETIRE_ST = (10, 3.0)
RETIRE_EMA = (5, 9)
RETIRE_EMA_CONST_SWITCH = dt.datetime(2026, 10, 8, 13, 0)   # 8.00 before, 2.00 after (logs 08-10)

_ONE_MIN = {}


def one_min(name, extra=None, full_session=False):
    """Clean 1-min spot (09:15-15:14 only, as both bots filter), optional extra rows appended.

    full_session=True keeps 09:15-15:30 for pricing exits after 15:15 (not for indicators).
    """
    if name not in _ONE_MIN:
        df = pd.read_parquet(f"{CLEAN}/{name}_1min_clean.parquet")
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df[df["datetime"] >= "2026-08-15"].copy()
        _ONE_MIN[name] = df
    df = _ONE_MIN[name]
    if extra is not None and not extra.empty:
        df = pd.concat([df, extra]).drop_duplicates("datetime", keep="first").sort_values("datetime")
    t = df["datetime"].dt.time
    end = dt.time(15, 30) if full_session else dt.time(15, 15)
    return df[(t >= dt.time(9, 15)) & (t < end)].reset_index(drop=True)


def trading_days(df):
    return sorted(set(df["datetime"].dt.date))


def nifty_day_bars(day, extra=None):
    """SENSEX 10-min bars for `day` with EMA34 bands, as nifty_ema34_signal builds them."""
    df = one_min("sensex", extra)
    days = trading_days(df)
    i = days.index(day)
    win = df[(df["datetime"].dt.date >= days[max(0, i - NIFTY_LOOKBACK_DAYS)]) & (df["datetime"].dt.date <= day)]
    rs = L.nifty["resample_complete_ohlcv"](win[["datetime", "open", "high", "low", "close"]], INTERVAL_MIN)
    rs = L.nifty["neutralize_cas_bar_wicks"](rs, L._quiet)
    rs = L.nifty["calculate_ema34_bands"](rs, period=34)
    rs["prev_close"] = rs["close"].shift(1)
    rs["prev_high"] = rs["high"].shift(1)
    rs["prev_low"] = rs["low"].shift(1)
    rs["prev_open"] = rs["open"].shift(1)
    rs["eval_time"] = rs["datetime"] + pd.Timedelta(minutes=INTERVAL_MIN)
    return rs


def nifty_gate(row, day, flag):
    """(side or None, stage) for one evaluation, mirroring nifty_ema34_trade's gate order."""
    side, _ = L.nifty["check_signal_against_bands"](
        live_ltp=row["close"], ema_high=row["ema_high"], ema_low=row["ema_low"],
        max_distance=NIFTY_MAX_DISTANCE, symbol="BSESEN", expiry_date="", base_diag_lines=[])
    if not side:
        return None, "band"
    ok, msg = L.nifty["evaluate_momentum_filter"](side, row.to_dict(), require_extreme_break=(flag == 1))
    if not ok:
        return None, "momentum"
    if row["datetime"].date() < day:
        return None, "prior-session"
    if row["eval_time"].time() >= NIFTY_ENTRY_CUTOFF:
        return None, "cutoff"
    return side, "pass"


def retire_day_bars(day, extra=None):
    """NIFTY 10-min bars for the 4-day window ending `day`, with ST and EMA5/9 as retire computes."""
    df = one_min("nifty", extra)
    days = trading_days(df)
    i = days.index(day)
    win = df[(df["datetime"].dt.date >= days[max(0, i - RETIRE_LOOKBACK_DAYS)]) & (df["datetime"].dt.date <= day)]
    rs = L.retire["resample_dataframe"](win[["datetime", "open", "high", "low", "close"]].assign(volume=0),
                                        INTERVAL_MIN, now_datetime=None, is_index=True)
    rs = L.retire["neutralize_cas_bar_wicks"](rs, L._quiet)
    rs = rs.reset_index(drop=True)
    st_df, _ = L.retire["compute_supertrend_stateful"](rs[["datetime", "high", "low", "close"]], *RETIRE_ST)
    rs = rs.merge(st_df[["datetime", "st"]], on="datetime", how="left")
    rs["ema_s"] = ta.ema(rs["close"], length=RETIRE_EMA[0])
    rs["ema_l"] = ta.ema(rs["close"], length=RETIRE_EMA[1])
    rs["ema_gap"] = rs["ema_s"] - rs["ema_l"]
    rs["prev_close"] = rs["close"].shift(1)
    rs["prev_high"] = rs["high"].shift(1)
    rs["prev_low"] = rs["low"].shift(1)
    rs["eval_time"] = rs["datetime"] + pd.Timedelta(minutes=INTERVAL_MIN)
    # A 15:05 bar is evaluated again at next day's 09:15 slot (retire does not drop prior-session bars).
    return rs


def retire_gate(row, flag):
    """(option_type or None, stage) mirroring retire_single_leg's flat-book gate order."""
    if pd.isna(row["st"]) or pd.isna(row["ema_gap"]):
        return None, "warmup"
    const = 8.0 if row["eval_time"] < RETIRE_EMA_CONST_SWITCH else 2.0
    if row["close"] > row["st"]:
        side, opt, ok_ema = "LONG", "PE", row["ema_s"] > row["ema_l"] + const
    elif row["close"] < row["st"]:
        side, opt, ok_ema = "SHORT", "CE", row["ema_s"] < row["ema_l"] - const
    else:
        return None, "st"
    if not ok_ema:
        return None, "ema"
    ok, _ = L.retire["evaluate_momentum_filter"](side, row.to_dict(), require_extreme_break=(flag == 1))
    if not ok:
        return None, "momentum"
    return opt, "pass"


def sensex_bars_from_nifty_log(log_path):
    """10-min SENSEX bars logged by the nifty bot (`UPDATED EMA BANDS ... Index OHLC`)."""
    pat = re.compile(r"UPDATED EMA BANDS .*Time=(\S+ \S+) \| Close=([\d.]+) \| EMA34_High=([\d.]+) \| "
                     r"EMA34_Low=([\d.]+) \| Index OHLC=\[O:([\d.]+), H:([\d.]+), L:([\d.]+), C:([\d.]+)\]")
    rows = {}
    for line in open(log_path, errors="replace"):
        if "Message logged" in line:
            continue
        m = pat.search(line)
        if m:
            g = m.groups()
            rows[g[0]] = dict(datetime=pd.Timestamp(g[0]), close=float(g[1]), ema_high=float(g[2]),
                              ema_low=float(g[3]), open=float(g[4]), high=float(g[5]), low=float(g[6]))
    return pd.DataFrame(sorted(rows.values(), key=lambda r: r["datetime"]))
