# Git + Codex + VM Deployment Cheat Sheet

## 1) Purpose

This document is the working runbook for:

- Coding from Mac or office PC (Codex cloud + GitHub)
- Moving code from GitHub to VMs
- Using Program_restart Google Sheet to deploy/pull code and download logs
- Keeping credentials safe (no token in repo/code/sheet)


## 2) Repositories

GitHub user: `vivekdesh`

Private repos:

- `selling`
- `whatsapp`
- `mod_rsi`
- `binance`
- `retire`
- `sensex`


## 3) Daily Mac Git Commands

Use from project folder:

```bash
cd /Users/vivek/ICICI_Direct/selling
git status
git add .
git commit -m "your comment"
git push
```

Shortcut functions in `~/.zshrc`:

```bash
gitsave selling "Updated selling logic"
gitsave mod_rsi
git_push_all "Daily backup"
git_push_all
git_pull_all
```

Notes:

- `git_push_all` commits and pushes all six repos (Mac -> GitHub).
- `git_pull_all` pulls all six repos (GitHub -> Mac).
- If no message is passed, auto message is used.


## 4) Office PC (Codex Cloud) Workflow

1. Open Codex cloud and connect GitHub.
2. Ask Codex to edit repo code.
3. Commit/push to GitHub.
4. On Mac, run `git_pull_all` to sync GitHub changes locally if needed.
5. Trigger VM deploy using Program_restart (`*_git_pull` rows).
5. If issue, fetch logs via Program_restart and paste logs to Codex cloud.

Important:

- Codex cloud cannot directly access Mac local folders.
- For runtime analysis, logs must be provided from Google Sheet output tabs.


## 5) Program_restart Commands Sheet

Sheet key:

`1vtvyqnWmt8ealS_XW8X2o5xM-CXXR6apyknfF8UP3MA`

Commands header in use:

`Command_ID | VM | Program | Clear_Logs | Execute | Logs_download | Log_Date | Log_From | Log_To | Status | Ack_Time | Ack_By | Result_Message`

### Git-pull command rows

Rows 28-35 (`Command_ID` 27-34):

- `27` `google_vm` `selling_git_pull`
- `28` `google_vm` `retire_git_pull`
- `29` `google_vm` `whatsapp_git_pull`
- `30` `oracle_vm` `mod_rsi_git_pull`
- `31` `oracle_vm` `selling_1_git_pull`
- `32` `oracle_vm` `sensex_git_pull`
- `33` `suresh_vm` `mod_rsi_git_pull`
- `34` `suresh_vm` `sensex_git_pull`

Run:

- Set `Execute=1` for the desired row.
- Agent sets it back to `0` after run.
- Check `Status` and `Result_Message`.

Behavior:

- Pull/deploy only
- No process restart
- No tmux restart


## 6) Deploy Mapping

Git-pull mapping used by Program_restart:

- `selling_git_pull` -> repo `selling` -> target `/home/deshpande_vivek/selling`
- `retire_git_pull` -> repo `retire` -> target `/home/deshpande_vivek/retire`
- `whatsapp_git_pull` -> repo `whatsapp` -> target `/home/deshpande_vivek/whatsapp`
- `mod_rsi_git_pull` (oracle) -> repo `mod_rsi` -> target `/home/ubuntu/mod_rsi`
- `selling_1_git_pull` -> repo `selling` -> target `/home/ubuntu/selling_1`
- `sensex_git_pull` (oracle) -> repo `sensex` -> target `/home/ubuntu/sensex`
- `mod_rsi_git_pull` (suresh) -> repo `mod_rsi` -> target `/home/ubuntu/mod_rsi`
- `sensex_git_pull` (suresh) -> repo `sensex` -> target `/home/ubuntu/sensex_suresh`

Excluded during deploy (preserved on VM):

- `*.json`
- `*.log`
- `*.log.py`
- `logs/`
- `__pycache__/`
- `venv/`
- `.venv/`
- `.git/`
- `.DS_Store`
- `gemini_log_update.tmp`


## 7) Program_restart Services

### Restart service after uploading Program_restart code

Google VM:

```bash
ssh vivek 'sudo systemctl restart program-restart-google.service'
ssh vivek 'sudo systemctl status program-restart-google.service --no-pager'
```

Oracle VM:

```bash
ssh oracle 'sudo systemctl restart program-restart-oracle.service'
ssh oracle 'sudo systemctl status program-restart-oracle.service --no-pager'
```

Suresh VM:

```bash
ssh suresh_oracle 'sudo systemctl restart program-restart-suresh.service'
ssh suresh_oracle 'sudo systemctl status program-restart-suresh.service --no-pager'
```

Check duplicate Google agent process:

```bash
ssh vivek 'ps -eo pid=,comm=,args= | grep "restart_agent.py --vm google_vm" | grep -v grep'
```


## 8) Sync Shortcuts (Mac)

Main:

```bash
all.u
all.d
```

Per target:

```bash
v.u
o.u
s.u
```

Current Suresh IP in active scripts:

`140.245.15.195`


## 9) GitHub Token Storage (VM)

Do not store token in:

- Git repo
- Program_restart code
- Google Sheet
- `change.txt`

Store on each VM user account via git credential helper.

Quick verification:

```bash
ssh oracle 'git ls-remote https://github.com/vivekdesh/mod_rsi.git HEAD'
ssh suresh_oracle 'git ls-remote https://github.com/vivekdesh/mod_rsi.git HEAD'
ssh vivek 'git ls-remote https://github.com/vivekdesh/selling.git HEAD'
```

If hashes return, credentials are valid.


## 10) Log Download for Codex Analysis

Use Commands sheet row for bot + VM:

- Set `Logs_download=1`
- Optional set `Log_Date`, `Log_From`, `Log_To`

Output sheets:

- `app_log`
- `app_single_log`

Copy relevant log lines and paste into Codex cloud for debugging.


## 11) Troubleshooting

### A) `fatal: could not read Username for 'https://github.com'`

Cause:

- VM service is non-interactive and Git credentials not stored.

Fix:

- Store GitHub credentials on VM user (`ubuntu` or `deshpande_vivek`) and re-test `git ls-remote`.

### B) Git-pull shows `DONE` but expected file not changed

Check:

1. Was that file committed/pushed to GitHub?
2. Did the pulled commit contain that file change?
3. Is file a JSON file? (`*.json` is intentionally excluded)

### C) Suresh sync timeout

Check active scripts use `140.245.15.195` and test:

```bash
ssh suresh_oracle 'hostname && pwd'
```


### D) Rename a commit message

Use `git commit --amend` when the commit you want to rename is the latest commit in the current repo.

Latest commit:

```bash
git commit --amend -m "New commit message"
git push --force-with-lease
```

Use interactive rebase when the commit is older than the latest commit.

Older commit:

```bash
git rebase -i HEAD~n
```

Meaning of `n`:

- `n = 1` means the latest commit
- `n = 2` means the latest 2 commits
- `n = 5` means the latest 5 commits

In the rebase editor:

- change `pick` to `reword` on the target commit line
- save and exit

If the editor is `vim`, use:

```text
i
```

- edit `pick` to `reword`
- press `Esc`
- type `:wq`
- press `Enter`

Git then opens the commit-message editor:

- replace the old message with the new message
- save and exit again

If that editor is also `vim`, use:

```text
i
```

- type the new message
- press `Esc`
- type `:wq`
- press `Enter`

Final push after rewording:

```bash
git push --force-with-lease
```

Short rule:

- latest commit message change: `git commit --amend`
- older commit message change: `git rebase -i HEAD~n`


## 12) Quick Test Sequence

1. Push code from Mac to GitHub:

```bash
gitsave selling "test deploy"
```

2. Pull all repos from GitHub to Mac (optional verify):

```bash
git_pull_all
```

3. In Commands sheet:

- Set `Execute=1` on `selling_1_git_pull` row (ID 31)

4. Verify:

- `Status = DONE`
- `Execute` reset to `0`
- No bot restart happened
