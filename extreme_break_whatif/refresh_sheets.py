#!/usr/bin/env python3
"""Read-only download of the sheets the extreme-break what-if needs, into ./sheets/.

Per bot (nifty, retire): Results, log_single, Log_backup -> 3 reads per bot, 6 in all,
with a pause between bots so the shared 60-reads/minute quota is never pressed.
Nothing is ever written to a sheet.
"""
import csv
import json
import os
import sys
import time

import gspread

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sheets")
BOTS = ("nifty", "retire")
TABS = ("Results", "log_single", "Log_backup")
PAUSE_BETWEEN_BOTS_SECONDS = 5


def refresh(bot):
    base = f"/Users/vivek/ICICI_Direct/{bot}"
    key = json.load(open(f"{base}/para.json"))["SPREADSHEET_KEY"]
    sh = gspread.service_account(filename=f"{base}/service_account.json").open_by_key(key)
    for tab in TABS:
        rows = sh.worksheet(tab).get_all_values()
        path = os.path.join(OUT, f"{bot}_{tab}.csv")
        with open(path + ".part", "w", newline="") as fh:
            csv.writer(fh).writerows(rows)
        os.replace(path + ".part", path)      # never leave a half-written CSV behind
        print(f"  {bot:6} {tab:11} {len(rows):6} rows")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n, b in enumerate(sys.argv[1:] or BOTS):
        if n:
            time.sleep(PAUSE_BETWEEN_BOTS_SECONDS)
        refresh(b)
