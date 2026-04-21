# ai-token-dashboard

The only token dashboard that covers all your AI agents.

One guy. $20/month. Every major AI agent. Fully monitored.

```
╔══════════════════════════════════════════════════════╗
║  Hermes  claude-sonnet-4-6                           ║
║  session: 20260411_070059_9f1335                     ║
╠══════════════════════════════════════════════════════╣
║  CONTEXT    ███████░░░░░░░░░░░░░░░   33.2%  ✓ healthy║
║  COST       ████░░░░░░░░░░░░░░░░░░   $0.84  (est)   ║
║  MESSAGES   ████████░░░░░░░░░░░░░░    8  (30+ = risk)║
║  VELOCITY   █████░░░░░░░░░░░░░░░░░  512 tok/msg      ║
╠══════════════════════════════════════════════════════╣
║  TOKEN BREAKDOWN                                     ║
║    Input (fresh):        12,440   @ $3.00/M          ║
║    Cache READ:           54,320   @ $0.30/M  ← cheap ║
║    Cache CREATED:           891   @ $3.75/M          ║
║    Output:                1,280   @ $15.00/M         ║
║    Total context:        67,651   / 200,000          ║
╠══════════════════════════════════════════════════════╣
║    Cache efficiency :  98.4%   (high = lower cost)   ║
║    Reasoning tokens :       0                        ║
║    Actual cost (API): $0.0821                        ║
║    Degradation risk : LOW   ✓  (Anthropic research)  ║
╠══════════════════════════════════════════════════════╣
║  →  session healthy — keep going                     ║
╚══════════════════════════════════════════════════════╝
```

---

## Why This Exists

AI agents don't show you what's happening to your tokens. You're flying blind on:

- How close you are to context limits
- What your session is actually costing
- Whether your prompt cache is working
- When to run `/compact` before accuracy degrades

Every major AI agent has this problem. Nobody had built one dashboard to cover all of them.

Until now.

---

## Supported Agents

| Agent | Status | Session Source |
|-------|--------|---------------|
| **Claude Code** | ✅ Full support | `~/.claude/projects/**/*.jsonl` |
| **Claude Code Desktop** | ✅ Full support | Same as Claude Code |
| **Hermes Agent** | ✅ Full support | `~/.hermes/state.db` (SQLite) |
| **Claw Code** | ✅ Full support | `~/.claw/sessions/**/*.jsonl` |
| **Gemini CLI** | ⚠️ Limited (Windows permission restriction) | `~/.gemini/history/*` |
| **Goose** | 🔜 Coming soon | Session format in progress |

---

## Four Ways to Use It

### 1. Python Dashboard — Visual, live, refreshes every 5s

```bash
# Claude Code (default)
python delivery/dashboard.py

# Hermes
python delivery/dashboard.py --agent hermes

# Gemini CLI
python delivery/dashboard.py --agent gemini

# All agents at once
python delivery/dashboard.py --all

# Single snapshot, no loop
python delivery/dashboard.py --agent hermes --once
```

### 2. CLI — One-shot from anywhere

```bash
python delivery/cli.py --agent cc
python delivery/cli.py --agent hermes
python delivery/cli.py --agent claw
python delivery/cli.py --agent all

# JSON output (pipe to other tools)
python delivery/cli.py --agent cc --json
```

### 3. MCP Server — Any agent calls it directly

```bash
python delivery/mcp_server.py
```

Any MCP-compatible agent gets three tools:
- `get_token_status` — context %, cost, risk, advice
- `get_token_detail` — full token breakdown
- `get_all_agents` — snapshot of all agents at once

No MCP package? Falls back to HTTP automatically:
```bash
python delivery/mcp_server.py --http
# GET http://localhost:7421/status?agent=hermes
# GET http://localhost:7421/all
```

### 4. Skill per agent — `/gauge` slash command

Copy the skill for your agent:

```bash
# Claude Code
cp skills/claude-code/SKILL.md ~/.claude/skills/gauge/SKILL.md

# Hermes
cp skills/hermes/SKILL.md ~/.hermes/skills/gauge/SKILL.md
```

Then run `/gauge` in your agent's terminal for an instant snapshot.

---

## Install

```bash
git clone https://github.com/albatrossflyon-coder/ai-token-dashboard
```

Requires Python 3.10+. Zero dependencies for the dashboard and CLI.

MCP server requires:
```bash
pip install mcp
```

---

## The Research Behind the Degradation Risk Gauge

Anthropic's own research identifies 5 failure modes in long AI sessions:

1. **"I don't know" circuit overridden** — competing signals cause false confidence
2. **Performative reasoning** — responses look right but the logic is wrong
3. **Sycophancy** — the AI agrees with your suggestion instead of checking independently
4. **Internal momentum** — can't self-correct mid-sentence
5. **Context decay** — early instructions fade, later ones dominate

Key thresholds:
- **Message 30+** — degradation starts
- **Context 50%** — plan to compact
- **Context 80%** — compact immediately

The degradation risk gauge is a direct implementation of this research. When it goes RED, trust your agent less and compact before continuing.

---

## What Each Gauge Means

| Gauge | Tracks |
|-------|--------|
| CONTEXT | % of context window used |
| COST | Cumulative session cost in USD |
| MESSAGES | Total assistant turns (30+ = degradation risk) |
| VELOCITY | Average output tokens per message |
| Cache READ | Tokens from prompt cache (10× cheaper than fresh input) |
| Cache CREATED | New cache writes (slightly more than fresh input) |
| Cache efficiency | `cache_read / (cache_read + cache_created)` — higher = cheaper |
| Degradation risk | Based on message count + context %. HIGH at 30+ messages or 80%+ context |

---

## The $20/Month Stack This Was Built For

This dashboard is part of the **claude-operator-kit** — a complete system for running professional-grade AI agent workflows on $20/month.

| Tool | Cost | Purpose |
|------|------|---------|
| Claude Pro | $20/month | The AI |
| ai-token-dashboard | Free | Token monitoring |
| fff | Free | Token-efficient file search |
| jCodeMunch + jDocMunch + jDataMunch | Free | Token-efficient code/doc/data navigation |
| jmunch-mcp | Free | MCP response compressor (88-99% reduction) |
| RTK | Free | Shell output compressor (60-90% reduction) |

**Total: $20/month.**

See: [claude-operator-kit](https://github.com/albatrossflyon-coder/claude-operator-kit)

---

## Credits & Tools Used

This dashboard wouldn't exist without these open-source projects:

| Tool | Author | What it does |
|------|--------|-------------|
| **fff** — Fast File Finder | [dmtrKovalenko](https://github.com/dmtrKovalenko/fff.nvim) | Frecency-ranked file search. Replaces bash find/grep. The tool that proved 50-75% token savings were possible. |
| **jCodeMunch MCP** | [jgravelle](https://github.com/jgravelle/jcodemunch-mcp) | Semantic code navigation via MCP. Reads symbols, not whole files. Core of the token-efficient stack. |
| **jDocMunch MCP** | [jgravelle](https://github.com/jgravelle/jdocmunch-mcp) | Section-level markdown navigation via MCP. Same author, same philosophy. |
| **jDataMunch MCP** | [jgravelle](https://github.com/jgravelle/jdatamunch-mcp) | Structured data navigation via MCP. Queries datasets, describes columns, samples rows — not raw file dumps. |
| **jmunch-mcp** | [jgravelle](https://github.com/jgravelle/jmunch-mcp) | MCP response compressor proxy. Wraps jCodeMunch, jDocMunch, jDataMunch and cuts their response token cost 88-99%. |
| **RTK** | [rtk-ai](https://github.com/rtk-ai/rtk) | Rust Token Killer. CLI proxy that compresses shell command output 60-90% before it hits your AI's context. |
| **Hermes Agent** | [NousResearch / Hermes team](https://github.com/NousResearch) | The AI agent whose state.db gave us the richest token data of any agent — including actual API cost and reasoning tokens. |
| **Claw Code** | [ultraworkers](https://github.com/ultraworkers/claw-code) | Open-source Rust parity implementation of Claude Code. Same JSONL session format — sessions in `~/.claw/sessions/`. |

**Research credit:**
The degradation risk thresholds (message 30+, context 80%) come from Anthropic's published research on long-context accuracy degradation. The sycophancy and performative reasoning failure modes are documented in their model safety research. This dashboard turns that research into a practical real-time signal.

---

## Pricing Reference

Prices used in cost calculations (update `core/parser.py` if Anthropic changes rates):

### Claude (Sonnet 4.6 / Opus 4.6)
| Token type | Per 1M tokens |
|-----------|--------------|
| Input (fresh) | $3.00 |
| Cache creation | $3.75 |
| Cache read | $0.30 |
| Output | $15.00 |

### Gemini
| Token type | Per 1M tokens |
|-----------|--------------|
| Input | $0.075 |
| Output | $0.30 |

---

## License

MIT — use it, fork it, ship it.

---

*Built by Chris Brown / Albatross AI*
*Part of the claude-operator-kit ecosystem*
