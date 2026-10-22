# extreme_break_whatif

What nifty and retire would have made with `Momentum_Extreme_Break_enabled = 1`
(flag = 0 has been live since 01-10-2026 ~13:15). Built 22-10-2026.

```bash
/Users/vivek/ICICI_Direct/MAC/extreme_break_whatif/run_daily.sh
```

Run it in the evening, after `clean.nosync` is updated and the VM logs are downloaded.
Output: `results/run_YYYY-MM-DD.txt`.

| File | Role |
|---|---|
| `livefuncs.py` | Pulls the bots' OWN gate functions from the master source (ast); never imports the bot modules |
| `bars.py` | Rebuilds every 10-min bar the way each bot does, from `/Users/vivek/Documents/nifty/data/clean.nosync` |
| `validate.py` | Replayed bars and verdicts vs the downloaded bot logs |
| `engine.py` | Sheet loaders, spot, IV from the bots' own fills, gate scanner |
| `engine2.py` | Sequential flag=1 timeline per bot + combined daily/cumulative table |
| `validate_sim.py` | Exit simulator vs every real chain (the calibration check) |
| `stress_test.py` | Bar-by-bar table and entry reproduction for chosen days |
| `sweep_sim.py` | Re-tunes the simulator variants (trail / auction freeze) |
| `refresh_sheets.py` | Read-only download of Results, log_single, Log_backup (6 reads) |
| `extreme_break_sheets.py` | Sheet signal parser (handles Log_backup's MM-DD date flips) |

Method, validation and traps: `/Users/vivek/ICICI_Direct/memory/extreme-break-whatif-tracker.md`.
