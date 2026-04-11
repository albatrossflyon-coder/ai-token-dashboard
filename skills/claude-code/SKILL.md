---
name: gauge
description: Instant token snapshot for the current Claude Code session — context %, cost, cache efficiency, degradation risk
---

Run a single token snapshot for the current Claude Code session and report back.

## Steps

1. Run the CLI:
```bash
python "C:/Users/albat/Desktop/Universal Brain/tools/ai-token-dashboard/delivery/cli.py" --agent cc
```

2. Read the output and report:
   - CONTEXT % and whether it's healthy / needs compact
   - Current session cost estimate
   - Degradation risk level
   - Advice line from the dashboard

3. If context is at 80%+ or messages are 30+, recommend running `/compact` immediately.

## Quick Reference
- GREEN = healthy, keep going
- YELLOW = plan to compact soon
- RED = compact now
- Degradation starts at message 30+ or 80% context (Anthropic research)
