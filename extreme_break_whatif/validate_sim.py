#!/usr/bin/env python3
"""Exit-simulator validation: push every REAL chain's own entry through the CF simulator
(no JOIN, no copying) and compare its exit time and chain P&L with what really happened.

If the simulator's stops, trailing, rollovers and force exits are right, the simulated
chain should land close to the real one. Run: python3 validate_sim.py nifty,retire
"""
import datetime as dt
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import engine as E
import engine2 as E2


def main(bot, start, end):
    w = E2.World(bot, start, end)
    import bars as B
    clean_last = max(B.trading_days(B.one_min(E.CFG[bot]["index"])))   # clean data only, no log rebuild
    rows, skipped = [], 0
    for ch in w.chains:
        l1 = ch["legs"][0]
        if not (start <= l1["entry"] < end):
            continue
        if ch["end"].date() > clean_last:
            skipped += 1        # no clean 1-min data yet for this chain: cannot be a calibration point
            continue
        before = sum(w.cf_pnl.values())
        w.log = []
        x_t, _ = w.run_position(l1["entry"], ch["signal"]["side"], follow=None)
        sim = sum(w.cf_pnl.values()) - before
        real = sum(l["pnl"] for l in ch["legs"])
        real_end = ch["end"]
        last = [x for x in w.log if "CF " in x and ("STOP" in x or "EXIT" in x or "TARGET" in x or "FLAT" in x or "still open" in x)]
        how = last[-1].strip().split(":")[0] if last else "?"
        rows.append((l1["entry"], ch["signal"]["side"], len(ch["legs"]), real, sim, real_end, x_t, ch["legs"][-1]["reason"], how))
    print(f"\n===== {bot.upper()} exit-simulator vs reality ({len(rows)} chains) =====")
    print(f"  {'entry':11} {'side':5} {'legs':>4} {'real':>9} {'sim':>9} {'diff':>8}  {'real end':11} {'sim end':11}  real reason | sim exit")
    abs_err = []
    for e, sd, n, real, sim, re_, se, rr, how in rows:
        abs_err.append(abs(sim - real))
        print(f"  {e:%d-%m %H:%M} {sd:5} {n:>4} {real:>9,.0f} {sim:>9,.0f} {sim-real:>+8,.0f}  {re_:%d-%m %H:%M} {se:%d-%m %H:%M}  {rr[:24]} | {how[:40]}")
    tot_r = sum(r[3] for r in rows)
    tot_s = sum(r[4] for r in rows)
    same_sign = sum(1 for r in rows if (r[3] >= 0) == (r[4] >= 0))
    print(f"  TOTAL real {tot_r:,.0f}  sim {tot_s:,.0f}  | mean |diff| {sum(abs_err)/len(abs_err):,.0f}  | same win/loss sign {same_sign}/{len(rows)}")
    if skipped:
        print(f"  ({skipped} chain(s) ending after {clean_last:%d-%m} excluded: clean 1-min data not updated yet)")


if __name__ == "__main__":
    E.install_log_bars()
    start, end = E.FLAG0_LIVE, dt.datetime.combine(dt.date.today(), dt.time(15, 30))
    for b in sys.argv[1].split(","):
        main(b, start, end)
