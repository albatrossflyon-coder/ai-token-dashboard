# /gauge — Claw Code Token Snapshot

Run this command inside a Claw Code session to get an instant token dashboard.

## Usage

```
/gauge
```

## What it does

Reads your current Claw Code session from `~/.claw/sessions/` and displays:
- Context % used (out of 200k limit)
- Estimated session cost in USD
- Message count + degradation risk (30+ messages = accuracy starts to degrade)
- Full token breakdown: input, cache read, cache write, output
- Cache efficiency % (higher = cheaper per token)
- Degradation risk level (LOW / MEDIUM / HIGH)

## How to install

```bash
cp skills/claw-code/SKILL.md ~/.claw/skills/gauge/SKILL.md
```

## Manual snapshot (no skill install needed)

From the ai-token-dashboard directory:

```bash
python delivery/cli.py --agent claw
```

## Session source

Reads from: `~/.claw/sessions/**/*.jsonl` (most recently modified file)
Also checks `./.claw/sessions/` if `~/.claw/sessions/` is empty.

## Notes

- Claw Code (ultraworkers/claw-code) uses the same JSONL session format as Claude Code.
- Full support: input tokens, output tokens, cache read, cache write, cost.
- Degradation thresholds are the same as CC (Anthropic research-backed).
