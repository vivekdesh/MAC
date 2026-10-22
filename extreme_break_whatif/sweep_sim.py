#!/usr/bin/env python3
import datetime as dt, warnings, io, contextlib
warnings.filterwarnings("ignore")
import engine as E, engine2 as E2, validate_sim as V
E.install_log_bars()
start, end = E.FLAG0_LIVE, dt.datetime.combine(dt.date.today(), dt.time(15, 30))
for bot in ("nifty", "retire"):
    for trail in (True, False):
        for cas in (True, False):
            E2.RULES[bot]["trail"] = trail
            E2.RULES[bot]["cas_freeze"] = cas
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                V.main(bot, start, end)
            last = [x for x in buf.getvalue().splitlines() if "TOTAL" in x][0]
            print(f"{bot:6} trail={trail!s:5} cas_freeze={cas!s:5} | {last.strip()}")
