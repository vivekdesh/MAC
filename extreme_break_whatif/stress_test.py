#!/usr/bin/env python3
"""Stress tests for the v2 replay on chosen days.

(a) bar-by-bar flag=0 / flag=1 verdicts for every flat evaluation slot of the day
(b) entry reproduction: replayed flag=0 entries on flat slots == actual fresh entries
(c) option re-pricing error: IV from the actual entry fill, re-priced at the actual exit
    spot/time, vs the actual exit fill (shows what entry-IV pricing can and cannot do)
"""
import datetime as dt
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import engine as E


def flat_at(legs, t):
    return not any(l["entry"] <= t < l["exit"] for l in legs)


def day_report(bot, day, legs, signals, gate, spot):
    print(f"\n--- {bot} {day:%d-%m-%Y} ---")
    actual_slots = {E.slot_of(s["t"]): s for s in signals if s["t"].date() == day}
    evals = gate.evals(day)
    if not evals:
        print("  no bars for this day (not in clean data / no log bars)")
        return
    hit = miss = extra = 0
    print(f"  {'slot':5} {'state':6} {'flag0':18} {'flag1':18} actual")
    for et, row in evals:
        d0 = gate.decide(row, et, 0)
        d1 = gate.decide(row, et, 1)
        act = actual_slots.get(et)
        state = "FLAT" if flat_at(legs, et) else "inpos"
        mark = ""
        if state == "FLAT":
            if d0[0] and act:
                hit += 1
                mark = "ENTRY  ✓ replay agrees"
            elif d0[0] and not act:
                extra += 1
                mark = "⚠ replay would enter, bot did not"
            elif act and not d0[0]:
                miss += 1
                mark = "⚠ bot entered, replay would not"
        elif act:
            mark = "(signal while a leg was open: rollover/overlap)"
        tag1 = "  <- flag=1 BLOCKS" if d0[0] and not d1[0] else ""
        print(f"  {et:%H:%M} {state:6} {str(d0[0] or d0[1]):18} {str(d1[0] or d1[1]):18} {mark}{tag1}")
    print(f"  entry reproduction: agree {hit}, bot-only {miss}, replay-only {extra}")


def pricing_check(bot, day, legs, spot):
    book = E.IVBook(legs, spot)
    print(f"\n  re-pricing check {bot} {day:%d-%m}: actual exit fill vs model (A) entry IV, (B) IV from OTHER fills nearby")
    errs_a, errs_b = [], []
    for n, l in enumerate(legs):
        if l["entry"].date() != day:
            continue
        S0, Sx = spot.at(l["entry"]), spot.at(l["exit"])
        if S0 is None or Sx is None:
            continue
        T0 = E.years_to_expiry(l["entry"], l["expiry"])
        Tx = E.years_to_expiry(l["exit"], l["expiry"])
        iv0 = E.implied_vol(l["px_in"], S0, l["strike"], T0, l["right"])
        ivx = E.implied_vol(l["px_out"], Sx, l["strike"], Tx, l["right"])
        if iv0 is None:
            print(f"    {l['entry']:%H:%M} IV not solvable")
            continue
        model = E.price(Sx, l["strike"], Tx, iv0, l["right"])
        err = model - l["px_out"]
        ivb = book.at(l["exit"], l["right"], l["expiry"], exclude=(n, "out"))
        mb = E.price(Sx, l["strike"], Tx, ivb, l["right"]) if ivb else None
        errb = (mb - l["px_out"]) if mb is not None else None
        errs_a.append(abs(err))
        if errb is not None:
            errs_b.append(abs(errb))
        print(f"    {l['entry']:%H:%M}->{l['exit']:%H:%M} {l['strike']}{l['right']} out {l['px_out']:.2f} | "
              f"A {model:.2f} ({err:+.2f}) | B {('n/a' if mb is None else f'{mb:.2f} ({errb:+.2f})')} | "
              f"IV in {iv0:.3f} exit-actual {ivx if ivx is None else round(ivx,3)} B {ivb if ivb is None else round(ivb,3)}")
    if errs_a:
        print(f"    mean |error| A {sum(errs_a)/len(errs_a):.2f} pts, B {(sum(errs_b)/len(errs_b)) if errs_b else float('nan'):.2f} pts")


def main(bot, days):
    E.install_log_bars()
    legs, signals = E.load_legs(bot), E.load_signals(bot)
    gate, spot = E.Gate(bot, E.EXTRA.get(E.CFG[bot]["index"])), E.Spot(E.CFG[bot]["index"])
    for d in days:
        day_report(bot, d, legs, signals, gate, spot)
        pricing_check(bot, d, legs, spot)


if __name__ == "__main__":
    ds = [dt.datetime.strptime(a, "%d-%m-%Y").date() for a in sys.argv[2:]]
    for b in sys.argv[1].split(","):
        main(b, ds)
