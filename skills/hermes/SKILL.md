---
name: gauge
description: Instant token snapshot for the current Hermes Agent session — reads from state.db
---

Run a single token snapshot for the current Hermes session and report back.

## Steps

1. Run the CLI:
```bash
python "C:/Users/albat/Desktop/Universal Brain/tools/ai-token-dashboard/delivery/cli.py" --agent hermes
```

2. Read the output and report:
   - CONTEXT % and whether it's healthy
   - Session cost (estimated + actual if available)
   - Reasoning tokens used (if any)
   - Cache efficiency
   - Degradation risk

3. Hermes stores actual API cost in state.db — report both estimated and actual if they differ significantly.

## Hermes-Specific Notes
- Data comes from `~/.hermes/state.db` (SQLite)
- Includes `reasoning_tokens` — extended thinking usage
- `actual_cost_usd` is available when billing provider confirms it
- Session title is stored — include it in the report for context
