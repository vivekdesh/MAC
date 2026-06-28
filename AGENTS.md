# Approval-First Workflow

For every task in this workspace:

1. Analyze and propose first.
2. Do not modify code, config, scripts, logs, or documentation until the user explicitly approves.
3. Before any implementation, show the exact code snippets or diffs that will be changed.
4. After approval, implement the change and run syntax, compile, or tests as appropriate.
5. After verification, propose the `change.txt` content for approval before updating it.
6. If `/Users/vivek/ICICI_Direct/gemini.md` exists, follow that file exactly for this workspace.

## Explanation Style

When explaining code logic or proposed changes, use simple human language first, then give a small practical example with sample flag values and expected result; avoid only technical terms because I may not understand the design from abstract wording alone.

## Log Analysis Source Rule

When analyzing today's bot behavior, trade signals, entries, exits, P&L, Google Sheet actions, or any issue related to what happened during the current trading day, first refer to the respective local Google folder logs for that bot.

Use the matching folder under `/Users/vivek/ICICI_Direct/Google/` based on the bot being discussed. Examples:
- `selling` bot: `/Users/vivek/ICICI_Direct/Google/selling/`
- `sensex` bot: `/Users/vivek/ICICI_Direct/Google/sensex/`
- `mod_rsi` bot: `/Users/vivek/ICICI_Direct/Google/mod_rsi/`
- `retire` bot: `/Users/vivek/ICICI_Direct/Google/retire/`
- `whatsapp` bot: `/Users/vivek/ICICI_Direct/Google/whatsapp/`

Use this rule when the user asks things like:
- "why signal generated today?"
- "why exit did not happen?"
- "check today's trades"
- "how much profit/loss?"
- "what happened at 09:54?"
- "why force sell/FBB did or did not trigger?"
- "analyze today's logs"

Do not use this rule when the question is only about future code design, general explanation, documentation wording, or static code review with no need to inspect today's runtime behavior.

Example:
If the user asks, "why SELL PE generated at 09:54 today?", inspect `/Users/vivek/ICICI_Direct/Google/selling/` logs first, then explain using the actual log sequence.

Counter-example:
If the user asks, "explain how force_sell_enabled should work," do not open today's Google logs unless the user also asks to compare with today's behavior.
