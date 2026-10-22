#!/usr/bin/env python3
"""v2 counterfactual: what Momentum_Extreme_Break_enabled=1 would have done, chain by chain.

For every actual fresh entry that flag=1 would have blocked (verified two ways: the
bot's own "break not required" text AND the replayed flag=1 gate on that bar), the bot
is flat from that bar under flag=1. The replay walks the following bars with the
flag=1 gate until the next actual fresh entry:

  NONE  no bar qualifies           -> chain removed, CF P&L = 0
  JOIN  same side qualifies while the actual leg is still open and it left by a
        non-stop reason (rollover, force, EOD, time roll) -> CF holds the same trade
        from a later price; later legs identical
  SIM   anything else              -> CF leg simulated minute by minute on clean
        1-min spot: option re-priced by Black-Scholes with the IV implied by the
        bot's own fill, stop = entry + SL_pts x delta (the bots' own formula),
        index SL / target, delta rollover; trailing stop NOT modelled (flagged)

All money figures are net of charges like the Results sheet: CF legs carry the
charge of the actual leg they replace.
"""
import csv
import datetime as dt
import os
import re
import sys
from bisect import bisect_right

import pandas as pd
from py_vollib.black_scholes import black_scholes as bs_price
from py_vollib.black_scholes.greeks.analytical import delta as bs_delta
from py_vollib.black_scholes.implied_volatility import implied_volatility as bs_iv

import bars as B

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, "sheets")          # refreshed by refresh_sheets.py
FLAG0_LIVE = dt.datetime(2026, 10, 1, 13, 20)   # last "intact" 13:15:21, first "not required" 14:25:24
RISK_FREE = 0.07                                # Risk_Free_Rate (retire params)
EXPIRY_CLOSE = dt.time(15, 30)
STRIKE_STEP = 100
ITM_STEPS = 1
CFG = {
    "nifty":  {"index": "sensex", "sl_pts": 153.0, "target_pts": None, "min_delta": 0.35, "latency_s": 20},
    "retire": {"index": "nifty",  "sl_pts": 60.0,  "target_pts": 170.0, "min_delta": 0.46, "latency_s": 25},
}
STOP_REASONS = ("STOPLOSS", "SL_HIT", "Stoploss")


# ---------------------------------------------------------------- sheet data
def _dt(s):
    s = (s or "").strip().lstrip("'")
    for f in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(s, f)
        except ValueError:
            pass
    return None


def _num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except ValueError:
        return None


def load_legs(bot):
    rows = list(csv.reader(open(f"{SHEETS}/{bot}_Results.csv")))[1:]
    legs = []
    for r in rows:
        if bot == "nifty":
            if len(r) < 13:
                continue
            et, xt = _dt(r[0]), _dt(r[1])
            m = re.match(r"\w+ (\d+) (CE|PE)", r[2].strip())
            if not (et and xt and m):
                continue
            legs.append(dict(entry=et, exit=xt, strike=int(m.group(1)), right=m.group(2),
                             expiry=dt.datetime.strptime(r[3].strip(), "%d-%b-%Y").date(),
                             side=r[4].strip(), qty=int(float(r[5])), px_in=_num(r[6]), px_out=_num(r[7]),
                             pnl=_num(r[8]), reason=r[9].strip(), charges=_num(r[12]) or 0.0))
        else:
            if len(r) < 16:
                continue
            et, xt = _dt(r[0]), _dt(r[1])
            det = (r[6] or r[7]).strip()
            m = re.match(r"NIFTY (\d+-\w+-\d{4}) (\d+)([CP])", det)
            if not (et and xt and m):
                continue
            right = "CE" if m.group(3) == "C" else "PE"
            legs.append(dict(entry=et, exit=xt, strike=int(m.group(2)), right=right,
                             expiry=dt.datetime.strptime(m.group(1), "%d-%b-%Y").date(),
                             side="SHORT" if right == "CE" else "LONG", qty=int(float(r[8])),
                             px_in=_num(r[2]), px_out=_num(r[3] if right == "CE" else r[4]),
                             pnl=_num(r[5]), reason=r[11].strip(), charges=_num(r[15]) or 0.0))
    return sorted([l for l in legs if l["exit"] >= FLAG0_LIVE - dt.timedelta(days=1)], key=lambda l: l["entry"])


def load_signals(bot):
    """Fresh-signal events (time, side, waived_by_text) from Log_backup + log_single CSVs."""
    sys.path.insert(0, HERE)
    import extreme_break_sheets as X
    X.START = FLAG0_LIVE - dt.timedelta(days=1)
    logs = list(csv.reader(open(f"{SHEETS}/{bot}_Log_backup.csv"))) + list(csv.reader(open(f"{SHEETS}/{bot}_log_single.csv")))
    out = []
    for t, side, waived, msg in X.signals(bot, logs):
        side = {"CE": "SHORT", "PE": "LONG"}.get(side, side)
        out.append(dict(t=t, side=side, waived_text=waived, msg=msg))
    return out


# ---------------------------------------------------------------- market data
def synth_from_nifty_log(day):
    """1-min rows that aggregate exactly to the 10-min SENSEX bars the nifty bot logged."""
    path = f"/Users/vivek/ICICI_Direct/Google/nifty/app_{day:%d%b%y}.log"
    try:
        lb = B.sensex_bars_from_nifty_log(path)
    except FileNotFoundError:
        return None
    lb = lb[lb["datetime"].dt.date == day]
    rows = []
    for _, r in lb.iterrows():
        for k in range(10):
            px = r["open"] if k == 0 else (r["high"] if k == 3 else (r["low"] if k == 6 else (r["close"] if k == 9 else None)))
            if px is None:
                px = r["close"] if k > 6 else r["open"]
            rows.append(dict(datetime=r["datetime"] + pd.Timedelta(minutes=k), open=px, high=px, low=px, close=px, volume=0))
    return pd.DataFrame(rows) if rows else None


EXTRA = {}


def install_log_bars(until=None):
    """Clean data lags a day: rebuild each missing SENSEX day (to `until`) from the nifty log.

    Returns the dates rebuilt. NIFTY (retire) has no logged OHLC, so its missing days stay
    empty and the engine falls back on the bot's own log text for those entries.
    """
    until = until or dt.date.today()
    last = max(B.trading_days(B.one_min("sensex")))
    frames, d = [], last + dt.timedelta(days=1)
    while d <= until:
        s = synth_from_nifty_log(d)
        if s is not None and not s.empty:
            frames.append(s)
        d += dt.timedelta(days=1)
    if frames:
        EXTRA["sensex"] = pd.concat(frames, ignore_index=True)
    return [f["datetime"].iloc[0].date() for f in frames]


class Spot:
    def __init__(self, name):
        df = B.one_min(name, EXTRA.get(name), full_session=True)
        self.t = list(df["datetime"])
        self.o, self.h, self.l, self.c = (list(df[k]) for k in ("open", "high", "low", "close"))

    def at(self, when):
        """Spot at a timestamp, linear inside the minute (open -> close)."""
        i = bisect_right(self.t, pd.Timestamp(when)) - 1
        if i < 0:
            return None
        frac = min(1.0, max(0.0, (pd.Timestamp(when) - self.t[i]).total_seconds() / 60.0))
        if (pd.Timestamp(when) - self.t[i]).total_seconds() > 120:
            return None     # no data at that time: never price off a stale print
        return self.o[i] + (self.c[i] - self.o[i]) * frac

    def minutes(self, start, end):
        i = bisect_right(self.t, pd.Timestamp(start))
        while i < len(self.t) and self.t[i] < pd.Timestamp(end):
            yield self.t[i], self.o[i], self.h[i], self.l[i], self.c[i]
            i += 1


def years_to_expiry(when, expiry):
    secs = (dt.datetime.combine(expiry, EXPIRY_CLOSE) - pd.Timestamp(when).to_pydatetime()).total_seconds()
    return max(secs, 60.0) / (365.0 * 86400.0)


def flag(right):
    return "c" if right == "CE" else "p"


def implied_vol(price, S, K, T, right):
    if S is None or price is None:
        return None
    try:
        return bs_iv(price, S, K, T, RISK_FREE, flag(right))
    except Exception:
        intrinsic = max(0.0, (S - K) if right == "CE" else (K - S))
        return 0.12 if price <= intrinsic else None


def price(S, K, T, iv, right):
    return bs_price(flag(right), S, K, T, RISK_FREE, iv)


def delta_abs(S, K, T, iv, right):
    return abs(bs_delta(flag(right), S, K, T, RISK_FREE, iv))


class IVBook:
    """IV implied by every actual fill of the bot (entries and exits), looked up by time.

    WHY: one entry IV drifts badly within a day (SENSEX 0.165-0.215 on 21-10); the
    bot's own fills are real market quotes, so the IV at any time is interpolated
    between the nearest fills of the same right and expiry.
    """

    def __init__(self, legs, spot):
        self.pts = []
        for n, l in enumerate(legs):
            for when, px, tag in ((l["entry"], l["px_in"], "in"), (l["exit"], l["px_out"], "out")):
                S = spot.at(when)
                if S is None or not px:
                    continue
                iv = implied_vol(px, S, l["strike"], years_to_expiry(when, l["expiry"]), l["right"])
                if iv and 0.03 < iv < 1.5:
                    self.pts.append((when, l["right"], l["expiry"], iv, (n, tag)))
        self.pts.sort(key=lambda p: p[0])

    def at(self, when, right, expiry, exclude=None):
        same = [p for p in self.pts if p[2] == expiry and p[4] != exclude and p[0].date() == when.date()]
        pool = [p for p in same if p[1] == right] or same
        if not pool:
            return None
        before = [p for p in pool if p[0] <= when]
        after = [p for p in pool if p[0] > when]
        if before and after:
            a, b = before[-1], after[0]
            w = (when - a[0]).total_seconds() / max(1.0, (b[0] - a[0]).total_seconds())
            return a[3] + (b[3] - a[3]) * w
        return (before[-1] if before else after[0])[3]


def strike_for(S, right):
    atm = round(S / STRIKE_STEP) * STRIKE_STEP
    return atm - ITM_STEPS * STRIKE_STEP if right == "CE" else atm + ITM_STEPS * STRIKE_STEP


def slot_of(t):
    """Evaluation slot (bar close) that produced a signal logged at t."""
    return ((pd.Timestamp(t) - pd.Timedelta(minutes=5)).floor("10min") + pd.Timedelta(minutes=5)).to_pydatetime()


# ---------------------------------------------------------------- gate evaluations
class Gate:
    def __init__(self, bot, extra=None):
        self.bot, self.extra, self.cache = bot, extra, {}

    def evals(self, day):
        """[(eval_time, row)] the bot evaluates on `day` while flat."""
        if day in self.cache:
            return self.cache[day]
        out = []
        try:
            if self.bot == "nifty":
                rs = B.nifty_day_bars(day, self.extra)
                for _, r in rs[rs["datetime"].dt.date == day].iterrows():
                    out.append((r["eval_time"].to_pydatetime(), r))
            else:
                rs = B.retire_day_bars(day, self.extra)
                prev = rs[rs["datetime"].dt.date < day]
                if not prev.empty:
                    out.append((dt.datetime.combine(day, dt.time(9, 15)), prev.iloc[-1]))
                for _, r in rs[rs["datetime"].dt.date == day].iterrows():
                    if r["eval_time"].time() <= dt.time(15, 15):
                        out.append((r["eval_time"].to_pydatetime(), r))
        except ValueError:
            out = []
        self.cache[day] = out
        return out

    def decide(self, row, when, flag_value):
        if self.bot == "nifty":
            side, stage = B.nifty_gate(row, when.date(), flag_value)
            return side, stage
        opt, stage = B.retire_gate(row, flag_value)
        if opt and when.time() > B.RETIRE_LAST_ENTRY:
            return None, "cutoff"
        return ({"CE": "SHORT", "PE": "LONG"}.get(opt), stage)

    def bar_for_signal(self, t):
        """Evaluation slot whose decision produced a fresh signal logged at t."""
        slot = (pd.Timestamp(t) - pd.Timedelta(minutes=5)).floor("10min") + pd.Timedelta(minutes=5)
        for et, row in self.evals(slot.date()):
            if et == slot.to_pydatetime():
                return et, row
        return None, None

    def scan(self, after, before, flag_value, allowed=None):
        day = after.date()
        while day <= before.date():
            for et, row in self.evals(day):
                if after < et < before and (allowed is None or allowed(et)):
                    side, stage = self.decide(row, et, flag_value)
                    if side:
                        return et, side, row
            day += dt.timedelta(days=1)
        return None, None, None


# ---------------------------------------------------------------- counterfactual
def simulate(bot, spot, start, S0, side, template, iv, until, qty, charges, log):
    """Short-option leg(s) from `start` until stop/target or `until`; delta rollover included."""
    c = CFG[bot]
    right = "CE" if side == "SHORT" else "PE"
    expiry = template["expiry"]
    K = strike_for(S0, right)
    T = years_to_expiry(start, expiry)
    p_in = price(S0, K, T, iv, right)
    d_in = delta_abs(S0, K, T, iv, right)
    trig = p_in + c["sl_pts"] * d_in
    idx_sl = S0 + c["sl_pts"] if right == "CE" else S0 - c["sl_pts"]
    idx_tg = None if not c["target_pts"] else (S0 - c["target_pts"] if right == "CE" else S0 + c["target_pts"])
    pnl, legs = 0.0, 1
    log.append(f"      SIM open  {start:%d-%m %H:%M:%S} {K}{right} S={S0:.2f} px={p_in:.2f} d={d_in:.3f} "
               f"optSL={trig:.2f} idxSL={idx_sl:.2f}" + (f" tgt={idx_tg:.2f}" if idx_tg else ""))
    for ts, o, h, l, cl in spot.minutes(start, until):
        worst = h if right == "CE" else l
        T = years_to_expiry(ts + pd.Timedelta(minutes=1), expiry)
        p_worst = price(worst, K, T, iv, right)
        hit_idx = (worst >= idx_sl) if right == "CE" else (worst <= idx_sl)
        if p_worst >= trig or hit_idx:
            exit_px = trig if p_worst >= trig else price(idx_sl, K, T, iv, right)
            pnl += (p_in - exit_px) * qty - charges
            log.append(f"      SIM stop  {ts:%d-%m %H:%M} worstS={worst:.2f} exit={exit_px:.2f} legP&L={(p_in-exit_px)*qty-charges:,.0f}")
            return pnl, ts.to_pydatetime(), legs, "stop"
        best = l if right == "CE" else h
        if idx_tg is not None and ((best <= idx_tg) if right == "CE" else (best >= idx_tg)):
            exit_px = price(idx_tg, K, T, iv, right)
            pnl += (p_in - exit_px) * qty - charges
            log.append(f"      SIM target {ts:%d-%m %H:%M} exit={exit_px:.2f} legP&L={(p_in-exit_px)*qty-charges:,.0f}")
            return pnl, ts.to_pydatetime(), legs, "target"
        p_cl = price(cl, K, T, iv, right)
        if delta_abs(cl, K, T, iv, right) < c["min_delta"]:
            pnl += (p_in - p_cl) * qty - charges
            log.append(f"      SIM roll  {ts:%d-%m %H:%M} S={cl:.2f} exit={p_cl:.2f} legP&L={(p_in-p_cl)*qty-charges:,.0f}")
            K = strike_for(cl, right)
            p_in = price(cl, K, T, iv, right)
            d_in = delta_abs(cl, K, T, iv, right)
            trig = p_in + c["sl_pts"] * d_in
            idx_sl = cl + c["sl_pts"] if right == "CE" else cl - c["sl_pts"]
            idx_tg = None if not c["target_pts"] else (cl - c["target_pts"] if right == "CE" else cl + c["target_pts"])
            legs += 1
    last = list(spot.minutes(until - dt.timedelta(minutes=1), until))
    S_end = last[-1][4] if last else S0
    p_end = price(S_end, K, years_to_expiry(until, expiry), iv, right)
    pnl += (p_in - p_end) * qty - charges
    log.append(f"      SIM still open at {until:%d-%m %H:%M} -> marked {p_end:.2f} legP&L={(p_in-p_end)*qty-charges:,.0f}")
    return pnl, until, legs, "open@next"


def counterfactual(bot, chain, next_t, gate, spot, log):
    leg1 = chain["legs"][0]
    c = CFG[bot]
    sig_t = chain["signal"]["t"]
    e0, row0 = gate.bar_for_signal(sig_t)
    v0 = gate.decide(row0, e0, 0) if row0 is not None else (None, "n/a")
    v1 = gate.decide(row0, e0, 1) if row0 is not None else (None, "n/a")
    log.append(f"    replay of signal bar {e0}: flag0={v0} flag1={v1}")
    e1, side1, _ = gate.scan(e0 or sig_t, next_t, 1)
    if e1 is None:
        log.append(f"    NONE: no flag=1 entry before next actual entry {next_t:%d-%m %H:%M}")
        return 0.0, "NONE", v1
    fill = e1 + dt.timedelta(seconds=c["latency_s"])
    S1 = spot.at(fill)
    S0 = spot.at(leg1["entry"])
    T0 = years_to_expiry(leg1["entry"], leg1["expiry"])
    iv0 = implied_vol(leg1["px_in"], S0, leg1["strike"], T0, leg1["right"])
    if iv0 is None or S1 is None:
        log.append(f"    flag=1 entry at {e1:%d-%m %H:%M} {side1} but no spot/IV to price it (S1={S1}, S0={S0}) -> UNPRICED")
        return None, "UNPRICED", v1
    log.append(f"    flag=1 entry at {e1:%d-%m %H:%M} {side1} (S={S1:.2f}); actual leg1 {leg1['entry']:%H:%M:%S} "
               f"S={S0:.2f} {leg1['strike']}{leg1['right']} @{leg1['px_in']} IV={iv0:.4f}")
    same_side = side1 == chain["signal"]["side"]
    non_stop_exit = not any(k in leg1["reason"] for k in STOP_REASONS)
    if same_side and fill < leg1["exit"] and non_stop_exit:
        K1 = strike_for(S1, leg1["right"])
        T1 = years_to_expiry(fill, leg1["expiry"])
        p1 = price(S1, K1, T1, iv0, leg1["right"])
        d1 = delta_abs(S1, K1, T1, iv0, leg1["right"])
        trig = p1 + c["sl_pts"] * d1
        Sx = spot.at(leg1["exit"])
        Tx = years_to_expiry(leg1["exit"], leg1["expiry"])
        ivx = implied_vol(leg1["px_out"], Sx, leg1["strike"], Tx, leg1["right"]) or iv0
        px_out = leg1["px_out"] if K1 == leg1["strike"] else price(Sx, K1, Tx, ivx, leg1["right"])
        # stop check between CF entry and the actual exit
        for ts, o, h, l, cl in spot.minutes(fill, leg1["exit"]):
            worst = h if leg1["right"] == "CE" else l
            if price(worst, K1, years_to_expiry(ts, leg1["expiry"]), iv0, leg1["right"]) >= trig:
                log.append(f"    JOIN broke: CF stop {trig:.2f} touched {ts:%H:%M} before actual exit -> SIM")
                return simulate(bot, spot, fill, S1, side1, leg1, iv0, next_t, leg1["qty"], leg1["charges"], log)[0], "SIM", v1
        leg_pnl = (p1 - px_out) * leg1["qty"] - leg1["charges"]
        rest = sum(l["pnl"] for l in chain["legs"][1:])
        log.append(f"    JOIN: CF {K1}{leg1['right']} in {p1:.2f} (actual {leg1['px_in']}), out {px_out:.2f} at "
                   f"{leg1['exit']:%H:%M:%S} [{leg1['reason']}] leg {leg_pnl:,.0f} (actual {leg1['pnl']:,.0f}) + later legs {rest:,.0f}")
        return leg_pnl + rest, "JOIN", v1
    total, kinds = 0.0, []
    while True:
        pnl, x_t, legs, how = simulate(bot, spot, fill, S1, side1, leg1, iv0, next_t, leg1["qty"], leg1["charges"], log)
        total += pnl
        kinds.append(f"{how},{legs}leg")
        if how == "open@next":
            break
        # flat again: re-entry waits for the next completed candle, then the flag=1 gate decides
        e1, side1, _ = gate.scan(x_t, next_t, 1)
        if e1 is None:
            break
        fill = e1 + dt.timedelta(seconds=c["latency_s"])
        S1 = spot.at(fill)
        log.append(f"    flag=1 re-entry at {e1:%d-%m %H:%M} {side1} (S={S1:.2f})")
    return total, "SIM(" + "; ".join(kinds) + ")", v1


def build_chains(bot, legs, signals):
    for l in legs:
        cands = [s for s in signals if s["side"] == l["side"] and s["t"] <= l["entry"] + dt.timedelta(seconds=90)]
        l["sig"] = cands[-1] if cands else None
    chains = {}
    for l in legs:
        if l["sig"] is not None:
            chains.setdefault(id(l["sig"]), {"signal": l["sig"], "legs": []})["legs"].append(l)
    return sorted(chains.values(), key=lambda c: c["signal"]["t"])


def run(bot, day_from, day_to, verbose=True):
    legs, signals = load_legs(bot), load_signals(bot)
    chains = build_chains(bot, legs, signals)
    gate, spot = Gate(bot, EXTRA.get(CFG[bot]["index"])), Spot(CFG[bot]["index"])
    all_sig_times = sorted(s["t"] for s in signals)
    results = []
    for ch in chains:
        t = ch["signal"]["t"]
        if not (day_from <= t.date() <= day_to) or t < FLAG0_LIVE:
            continue
        e0, row0 = gate.bar_for_signal(t)
        replay_waived = None
        if row0 is not None:
            replay_waived = bool(gate.decide(row0, e0, 0)[0]) and not gate.decide(row0, e0, 1)[0]
        if not ch["signal"]["waived_text"] and not replay_waived:
            continue
        actual = sum(l["pnl"] for l in ch["legs"])
        later = [x for x in all_sig_times if x > t + dt.timedelta(seconds=60)]
        next_t = later[0] if later else dt.datetime.combine(day_to + dt.timedelta(days=1), dt.time(9, 15))
        next_t = slot_of(next_t)
        log = [f"  {t:%d-%m %H:%M:%S} {ch['signal']['side']:5} actual chain {actual:,.0f} over {len(ch['legs'])} leg(s); "
               f"waived text={ch['signal']['waived_text']} replay={replay_waived}; next actual entry {next_t:%d-%m %H:%M}"]
        cf, kind, _ = counterfactual(bot, ch, next_t, gate, spot, log)
        results.append(dict(t=t, actual=actual, cf=cf, kind=kind, text=ch["signal"]["waived_text"], replay=replay_waived))
        if verbose:
            print("\n".join(log))
            print(f"    => CF {cf if cf is None else round(cf):,} | flag=1 effect {('n/a' if cf is None else f'{cf-actual:+,.0f}')}  [{kind}]\n")
    return results


if __name__ == "__main__":
    install_log_bars()
    d0 = dt.datetime.strptime(sys.argv[2], "%d-%m-%Y").date()
    d1 = dt.datetime.strptime(sys.argv[3], "%d-%m-%Y").date()
    for b in sys.argv[1].split(","):
        print(f"===== {b.upper()} {d0:%d-%m} .. {d1:%d-%m} =====")
        res = run(b, d0, d1)
        tot = sum((r["cf"] - r["actual"]) for r in res if r["cf"] is not None)
        print(f"  TOTAL flag=1 effect {tot:+,.0f} over {len(res)} chain(s)\n")
