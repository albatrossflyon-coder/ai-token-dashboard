---
name: gauge
description: Token snapshot for the current Gemini CLI session
---

Run a token snapshot for the current Gemini CLI session.

## Steps

1. Run the CLI:
```bash
python "C:/Users/albat/Desktop/Universal Brain/tools/ai-token-dashboard/delivery/cli.py" --agent gemini
```

2. If successful, report context %, cost, and message count.

3. If permission error: Gemini CLI history files are locked on Windows. Tell the user:
   > "Gemini history files are permission-restricted on Windows. Run from an elevated terminal or use the /usage command in Gemini CLI directly."

## Gemini-Specific Notes
- History files are in `~/.gemini/history/` — hash-named, no extension
- Gemini context windows are much larger (1M-2M tokens) — context % will read low
- Pricing is significantly cheaper than Claude ($0.075/M input vs $3.00/M)
- Token data format: `usageMetadata.promptTokenCount` / `candidatesTokenCount`
