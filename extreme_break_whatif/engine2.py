#!/usr/bin/env python3
"""v2 sequential counterfactual: one flag=1 timeline per bot, replayed against the real one.

Timeline rules (CF = counterfactual bot running Momentum_Extreme_Break_enabled=1):
  * at each real fresh entry: CF busy -> real chain does not happen in CF;
    CF flat and flag=1 passes on that bar -> CF takes the REAL chain (copied exactly);
    CF flat and flag=1 blocks -> CF stays flat.
  * while CF is flat between real entries, every bar is replayed with the flag=1 gate
    (the bots' own code, validated against their logs); a pass opens a CF position.
  * a CF position is simulated minute by minute on clean 1-min spot with the bots' own
    rules: initial stop SL_pts from entry, trailing (nifty 36/0.74 + breakeven 132,
    retire 4/1.1 capped at target), stop order = option + delta x distance (tightens
    only), retire 170-pt target and SuperTrend exit, delta rollover, 11:30 expiry-day
    roll, square-off before a non-trading day (from 16-10), and the user's manual force
    exits (both bots were force-closed at the same seconds on 16-10, so they are the
    user's calls and are applied to a CF position open at that moment).
  * JOIN: if a real leg of the same side is open while CF holds, CF follows it: when the
    real leg leaves by a non-stop reason CF leaves too (same price if same strike) and,
    after a rollover, CF holds the identical new legs (copied).
Prices: Black-Scholes with the IV implied by the bot's own nearest fills (IVBook).
"""
import datetime as dt
import sys
import warnings
from collections import defaultdict

warnings.filterwarnings("ignore", category=DeprecationWarning)

import pandas as pd

import bars as B
import engine as E

ROLL_REASONS = ("ROLLOVER", "Rollover")
STOP_REASONS = ("STOPLOSS", "SL_HIT", "Stoploss")
MANUAL_REASONS = ("FORCE_EXIT", "Force Buy-Back")
NO_CARRY_FROM = dt.date(2026, 10, 16)          # no-carry-before-non-trading-day deployed 16-10
EXPIRY_ROLL_TIME = dt.time(11, 30)             # Time_Rollover_time / Tuesday_Rollover_time
RULES = {
    # trail / cas_freeze / daily_exit chosen by validate_sim.py against all real chains (22-10-2026)
    "nifty":  dict(sl=153.0, step=36.0, ratio=0.74, breakeven=132.0, target=None, st_exit=False,
                   eod_flat=dt.time(15, 14), min_delta=0.35, trail=False, cas_freeze=True, daily_exit=None),
    "retire": dict(sl=60.0, step=4.0, ratio=1.1, breakeven=None, target=170.0, st_exit=True,
                   eod_flat=dt.time(15, 10), min_delta=0.46, trail=True, cas_freeze=True,
                   daily_exit=dt.time(15, 20)),
}


class World:
    def __init__(self, bot, start, end):
        self.bot, self.start, self.end = bot, start, end
        self.r = RULES[bot]
        self.legs = E.load_legs(bot)
        self.signals = E.load_signals(bot)
        self.chains = E.build_chains(bot, self.legs, self.signals)
        for ch in self.chains:
            ch["slot"] = E.slot_of(ch["signal"]["t"])
            ch["end"] = max(l["exit"] for l in ch["legs"])
        self.gate = E.Gate(bot, E.EXTRA.get(E.CFG[bot]["index"]))
        self.spot = E.Spot(E.CFG[bot]["index"])
        self.iv = E.IVBook(self.legs, self.spot)
        self.qty = self.legs[-1]["qty"]
        ch_sorted = sorted(l["charges"] for l in self.legs if l["charges"])
        self.charge = ch_sorted[len(ch_sorted) // 2]
        self.expiries = sorted({l["expiry"] for l in self.legs})
        self.manual = sorted(l["exit"] for l in self.legs if any(k in l["reason"] for k in MANUAL_REASONS))
        self.trading_days = set(B.trading_days(B.one_min(E.CFG[bot]["index"], E.EXTRA.get(E.CFG[bot]["index"]))))
        self.log = []
        self.cf_pnl = defaultdict(float)     # by exit date
        self.notes = []

    # ------------------------------------------------------------ helpers
    def expiry_for(self, when, right):
        """Nearest expiry still tradeable at `when` (expiry day rolls at 11:30)."""
        for e in self.expiries:
            if e > when.date() or (e == when.date() and when.time() < EXPIRY_ROLL_TIME):
                return e
        return self.expiries[-1]

    def P(self, S, K, when, expiry, right):
        T = E.years_to_expiry(when, expiry)
        iv = self.iv.at(when, right, expiry) or self.iv.at(when, "CE" if right == "PE" else "PE", expiry) or 0.18
        return E.price(S, K, T, iv, right), E.delta_abs(S, K, T, iv, right)

    def next_is_trading(self, day):
        d = day + dt.timedelta(days=1)
        for _ in range(5):
            if d.weekday() < 5:
                return d in self.trading_days or d > max(self.trading_days)
            d += dt.timedelta(days=1)
        return True

    def book(self, when, pnl, what):
        self.cf_pnl[when.date()] += pnl
        self.log.append(f"      {what}: {pnl:+,.0f}")

    # ------------------------------------------------------------ CF position
    def run_position(self, entry_t, side, follow=None):
        """Simulate a CF short-option position from entry_t. Returns exit time."""
        r = self.r
        right = "CE" if side == "SHORT" else "PE"
        sgn = 1 if right == "CE" else -1            # index move that hurts a short CE is +
        S = self.spot.at(entry_t)
        if S is None:
            self.notes.append(f"{entry_t:%d-%m %H:%M} no spot -> CF entry skipped")
            return entry_t, None
        expiry = self.expiry_for(entry_t, right)
        K = E.strike_for(S, right)
        p_in, d_in = self.P(S, K, entry_t, expiry, right)
        p_in_fill = p_in
        idx_entry, idx_sl0 = S, S + sgn * r["sl"]
        idx_sl, trig = idx_sl0, p_in + d_in * r["sl"]
        tgt = None if not r["target"] else S - sgn * r["target"]
        mfe, steps = 0.0, 0
        self.log.append(f"    CF OPEN {entry_t:%d-%m %H:%M:%S} {side} {K}{right} exp {expiry:%d-%m} S={S:.2f} "
                        f"px={p_in:.2f} d={d_in:.3f} stop={trig:.2f} idxSL={idx_sl:.2f}"
                        + (f" tgt={tgt:.2f}" if tgt else "") + (f" [JOIN real {follow['strike']}{follow['right']} "
                        f"{follow['entry']:%H:%M}->{follow['exit']:%H:%M} {follow['reason']}]" if follow else ""))
        manual = [m for m in self.manual if m > entry_t]
        prev_t = entry_t
        for ts, o, h, l, c in self.spot.minutes(entry_t, self.end):
            ts = ts.to_pydatetime()
            if r.get("daily_exit") and ts.time() >= r["daily_exit"]:
                # retire leaves every day at ~15:20 (Results: 'Stoploss Triggered' 15:20 on 01,08,09,12,13,14 Oct)
                last_good = self.spot.at(dt.datetime.combine(ts.date(), dt.time(15, 14))) or c
                px = self.P(last_good, K, ts, expiry, right)[0]
                self.book(ts, (p_in_fill - px) * self.qty - self.charge, f"CF DAILY EXIT {ts:%d-%m %H:%M} px={px:.2f}")
                return ts, None
            if r.get("cas_freeze", True) and ts.time() >= dt.time(15, 15):
                continue        # closing-auction prints: both bots freeze index-driven logic (CAS option-only window)
            # real leg we follow leaves by a non-stop reason -> CF leaves with it
            if follow and ts >= follow["exit"]:
                if not any(k in follow["reason"] for k in STOP_REASONS):
                    if follow["strike"] == K and follow["expiry"] == expiry:
                        px = follow["px_out"]
                    else:
                        px = self.P(self.spot.at(follow["exit"]) or c, K, follow["exit"], expiry, right)[0]
                    self.book(follow["exit"], (p_in_fill - px) * self.qty - self.charge,
                              f"CF EXIT {follow['exit']:%d-%m %H:%M:%S} with real leg [{follow['reason']}] px={px:.2f}")
                    return follow["exit"], follow
                follow = None   # real leg stopped out at ITS level; CF keeps its own stop
            # gap / stop (checked before this minute's favourable move)
            adverse = h if sgn > 0 else l
            p_adverse = self.P(adverse, K, ts, expiry, right)[0]
            gap_through = (o - idx_sl) * sgn >= 0
            if gap_through:
                # opened beyond the stop: filled at the open market price, never better than the trigger
                px = max(trig, self.P(o, K, ts, expiry, right)[0])
                kind = "GAP STOP"
            elif p_adverse >= trig:
                px, kind = trig, "OPTION STOP"           # broker stop order fires at its trigger
            elif (adverse - idx_sl) * sgn >= 0:
                px, kind = self.P(idx_sl, K, ts, expiry, right)[0], "INDEX STOP"   # software exit at market
            else:
                px = None
            if px is not None:
                self.book(ts, (p_in_fill - px) * self.qty - self.charge,
                          f"CF {kind} {ts:%d-%m %H:%M} idxSL={idx_sl:.2f} trig={trig:.2f} fill={px:.2f}")
                return ts, None
            fav = l if sgn > 0 else h
            if tgt is not None and (fav - tgt) * sgn <= 0:
                px = self.P(tgt, K, ts, expiry, right)[0]
                self.book(ts, (p_in_fill - px) * self.qty - self.charge, f"CF TARGET {ts:%d-%m %H:%M} px={px:.2f}")
                return ts, None
            # trailing on max favourable excursion
            mfe = max(mfe, (idx_entry - fav) * sgn) if r.get("trail", True) else 0.0
            n = int(mfe // r["step"])
            cand = idx_sl
            if n > steps:
                cand = idx_sl0 - sgn * n * (r["step"] / r["ratio"])
                if tgt is not None and (cand - tgt) * sgn <= 0:
                    cand = tgt + sgn * r["step"]
                steps = n
            if r["breakeven"] and mfe >= r["breakeven"]:
                cand = min(cand, idx_entry) if sgn > 0 else max(cand, idx_entry)
            if (cand - idx_sl) * sgn < 0:
                idx_sl = round(cand, 1)
                pc, dc = self.P(c, K, ts, expiry, right)
                new_trig = pc + dc * abs(c - idx_sl)
                if new_trig < trig:
                    trig = new_trig
            # manual force exit by the user at this minute
            if manual and ts >= manual[0]:
                px = self.P(c, K, ts, expiry, right)[0]
                self.book(ts, (p_in_fill - px) * self.qty - self.charge, f"CF MANUAL FORCE EXIT {ts:%d-%m %H:%M} px={px:.2f}")
                return ts, None
            # square-off before a non-trading day (from 16-10)
            if ts.date() >= NO_CARRY_FROM and ts.time() >= r["eod_flat"] and not self.next_is_trading(ts.date()):
                px = self.P(c, K, ts, expiry, right)[0]
                self.book(ts, (p_in_fill - px) * self.qty - self.charge, f"CF EOD FLAT (non-trading next) {ts:%d-%m %H:%M} px={px:.2f}")
                return ts, None
            # retire SuperTrend exit at each evaluation slot
            if r["st_exit"] and ts.minute % 10 == 5 and ts.second == 0:
                for et, row in self.gate.evals(ts.date()):
                    if et == ts and not pd.isna(row["st"]):
                        if (row["close"] - row["st"]) * sgn > 0:
                            px = self.P(c, K, ts, expiry, right)[0]
                            self.book(ts, (p_in_fill - px) * self.qty - self.charge, f"CF ST EXIT {ts:%d-%m %H:%M} px={px:.2f}")
                            return ts, None
            # rollovers (only when not following a real leg, which carries its own)
            roll = None
            pc, dc = self.P(c, K, ts, expiry, right)
            if follow is None and dc < r["min_delta"]:
                roll = "delta"
            if follow is None and ts.date() == expiry and ts.time() >= EXPIRY_ROLL_TIME:
                roll = "expiry-day"
            if roll:
                self.book(ts, (p_in_fill - pc) * self.qty - self.charge, f"CF ROLL({roll}) {ts:%d-%m %H:%M} {K}{right} px={pc:.2f}")
                expiry = self.expiry_for(ts + dt.timedelta(minutes=1), right)
                K = E.strike_for(c, right)
                p_in_fill, d_in = self.P(c, K, ts, expiry, right)
                idx_entry, idx_sl0 = c, c + sgn * r["sl"]
                idx_sl, trig = idx_sl0, p_in_fill + d_in * r["sl"]
                tgt = None if not r["target"] else c - sgn * r["target"]
                mfe, steps = 0.0, 0
                self.log.append(f"      CF re-open {K}{right} exp {expiry:%d-%m} px={p_in_fill:.2f} stop={trig:.2f}")
            prev_t = ts
        px = self.P(self.spot.at(prev_t) or idx_entry, K, prev_t, expiry, right)[0]
        self.book(prev_t, (p_in_fill - px) * self.qty, f"CF still open at data end {prev_t:%d-%m %H:%M}, marked {px:.2f}")
        return self.end, None

    def cf_may_enter(self, when):
        """A NEW CF entry is possible only on a bar where the real bot was in a trade.

        WHY: flag=1 is strictly tighter than flag=0. Where the real bot was flat and did
        not enter, something blocked it (gate, re-entry wait, stale/pending order state,
        retire's 09:15 premium check) and the same block applies to the CF bot; only a bar
        the real bot never evaluated (it was holding) can give the CF bot a new entry.
        Retire's 09:15 slot runs an option-premium candle check that cannot be replayed.
        """
        if self.bot == "retire" and when.time() == dt.time(9, 15):
            return False
        return any(l["entry"] <= when < l["exit"] for l in self.legs)

    def real_leg_open(self, when, side):
        for l in self.legs:
            if l["entry"] <= when < l["exit"] and l["side"] == side:
                return l
        return None

    def chain_of(self, leg):
        for ch in self.chains:
            if leg in ch["legs"]:
                return ch
        return None

    # ------------------------------------------------------------ timeline
    def run(self):
        chains = [c for c in self.chains if self.start <= c["slot"] < self.end or (c["slot"] < self.start < c["end"])]
        busy_until, cursor = self.start, self.start
        i = 0
        while i < len(chains) or cursor < self.end:
            nxt = chains[i] if i < len(chains) else None
            horizon = nxt["slot"] if nxt else self.end
            if busy_until <= horizon and cursor < horizon:
                e1, side1, _ = self.gate.scan(max(cursor, busy_until), horizon, 1, allowed=self.cf_may_enter)
                if e1 is not None:
                    fill = e1 + dt.timedelta(seconds=E.CFG[self.bot]["latency_s"])
                    self.log.append(f"  {e1:%d-%m %H:%M} flag=1 gate passes {side1} while CF flat (real bot: "
                                    f"{'in a trade' if self.real_leg_open(e1, side1) or self.real_leg_open(e1, 'LONG' if side1 == 'SHORT' else 'SHORT') else 'FLAT - should not happen'})")
                    follow = self.real_leg_open(fill, side1)
                    x_t, rolled_leg = self.run_position(fill, side1, follow)
                    if rolled_leg is not None and any(k in rolled_leg["reason"] for k in ROLL_REASONS):
                        ch = self.chain_of(rolled_leg)
                        rest = [l for l in ch["legs"] if l["entry"] >= rolled_leg["exit"]]
                        for l in rest:
                            self.book(l["exit"], l["pnl"], f"CF holds real rollover leg {l['strike']}{l['right']} {l['entry']:%H:%M}->{l['exit']:%d-%m %H:%M} [{l['reason']}]")
                        x_t = max([x_t] + [l["exit"] for l in rest])
                    busy_until = cursor = x_t
                    continue
                cursor = horizon
            if nxt is None:
                break
            ch = nxt
            i += 1
            actual = sum(l["pnl"] for l in ch["legs"])
            e0, row0 = self.gate.bar_for_signal(ch["signal"]["t"])
            if ch["slot"] < self.start:
                passes = True       # already running when the window opens
            elif row0 is None:
                passes = not ch["signal"]["waived_text"]     # no clean bar (22-10 NIFTY): bot's own text decides
                self.notes.append(f"{ch['slot']:%d-%m %H:%M} no replay bar; used log text (waived={ch['signal']['waived_text']})")
            else:
                passes = bool(self.gate.decide(row0, e0, 1)[0]) and not ch["signal"]["waived_text"]
            tag = f"  {ch['slot']:%d-%m %H:%M} REAL {ch['signal']['side']:5} chain {actual:+,.0f} ({len(ch['legs'])} leg)"
            if busy_until > ch["slot"]:
                self.log.append(f"{tag} -> CF BUSY until {busy_until:%d-%m %H:%M}: chain does not happen in CF")
                continue
            if passes:
                self.log.append(f"{tag} -> flag=1 also takes it: copied")
                for l in ch["legs"]:
                    self.book(l["exit"], l["pnl"], f"copy leg {l['strike']}{l['right']} [{l['reason']}]")
                busy_until = cursor = ch["end"]
            else:
                self.log.append(f"{tag} -> BLOCKED by flag=1 (text waived={ch['signal']['waived_text']})")
                cursor = ch["slot"]
        return self

    def actual_by_day(self):
        out = defaultdict(float)
        for l in self.legs:
            if self.start <= l["exit"] < self.end or (l["exit"] >= self.start and l["entry"] < self.start):
                out[l["exit"].date()] += l["pnl"]
        return out


def report(bot, start, end):
    w = World(bot, start, end).run()
    print(f"\n===== {bot.upper()}  {start:%d-%m %H:%M} -> {end:%d-%m %H:%M} =====")
    print("\n".join(w.log))
    for n in w.notes:
        print("  NOTE", n)
    act = w.actual_by_day()
    days = sorted(set(act) | set(w.cf_pnl))
    print(f"\n  {'Date':10} {'Actual':>10} {'Flag=1':>10} {'Diff':>9} {'CumActual':>11} {'CumFlag=1':>11} {'CumDiff':>9}")
    ca = cf = 0.0
    for d in days:
        ca += act.get(d, 0.0)
        cf += w.cf_pnl.get(d, 0.0)
        print(f"  {d:%d-%m-%Y} {act.get(d,0):>10,.0f} {w.cf_pnl.get(d,0):>10,.0f} {w.cf_pnl.get(d,0)-act.get(d,0):>+9,.0f} "
              f"{ca:>11,.0f} {cf:>11,.0f} {cf-ca:>+9,.0f}")
    return w


def combined(worlds):
    """Daily and cumulative flag=1 effect across bots (+ = flag=1 better)."""
    diff = defaultdict(lambda: defaultdict(float))
    for w in worlds:
        act = w.actual_by_day()
        for d in set(act) | set(w.cf_pnl):
            diff[d][w.bot] = w.cf_pnl.get(d, 0.0) - act.get(d, 0.0)
    bots = [w.bot for w in worlds]
    print("\n===== COMBINED flag=1 effect (+ = flag=1 better) =====")
    print("  " + f"{'Date':10} " + " ".join(f"{b:>9}" for b in bots) + f" {'Day':>9} {'Cumulative':>11}")
    cum = 0.0
    for d in sorted(diff):
        day = sum(diff[d].values())
        cum += day
        print("  " + f"{d:%d-%m-%Y} " + " ".join(f"{diff[d].get(b, 0.0):>+9,.0f}" for b in bots) + f" {day:>+9,.0f} {cum:>+11,.0f}")
    return cum


if __name__ == "__main__":
    rebuilt = E.install_log_bars()
    if rebuilt:
        print("SENSEX days rebuilt from nifty log bars (not yet in clean data): " + ", ".join(f"{d:%d-%m}" for d in rebuilt))
    start = dt.datetime.strptime(sys.argv[2], "%d-%m-%Y %H:%M")
    end = dt.datetime.strptime(sys.argv[3], "%d-%m-%Y %H:%M")
    combined([report(b, start, end) for b in sys.argv[1].split(",")])
