"""
parser.py — AI Token Dashboard
Detects and reads session data for each supported AI agent.

Supported:
  - Claude Code (CC)         ~/.claude/projects/**/*.jsonl
  - Claude Code Desktop      same path as CC (same session format)
  - Hermes Agent             ~/.hermes/state.db  (SQLite)
  - Claw Code                ~/.claw/sessions/**/*.jsonl  (ultraworkers/claw-code)
  - Gemini CLI               ~/.gemini/history/* (permission-restricted — limited support)
  - Goose                    not yet available — session format TBD
"""

import json
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

# ── Model context limits ──────────────────────────────────────────────────────
MODEL_LIMITS = {
    "claude-sonnet-4-6": 200_000,
    "claude-opus-4-6":   200_000,
    "claude-haiku-4-5":  200_000,
    "gemini-2.0-flash":  1_000_000,
    "gemini-1.5-pro":    2_000_000,
    "gemini-1.5-flash":  1_000_000,
}
DEFAULT_LIMIT = 200_000

# ── Pricing per million tokens (USD) ─────────────────────────────────────────
PRICING = {
    "claude": {
        "input":          3.00,
        "cache_creation": 3.75,
        "cache_read":     0.30,
        "output":        15.00,
    },
    "gemini": {
        "input":  0.075,
        "output": 0.30,
    },
}


@dataclass
class SessionData:
    agent:         str   = "unknown"
    model:         str   = "unknown"
    session_file:  str   = ""
    input_tokens:  int   = 0
    output_tokens: int   = 0
    cache_read:    int   = 0
    cache_write:   int   = 0
    total_context: int   = 0
    context_limit: int   = DEFAULT_LIMIT
    context_pct:   float = 0.0
    messages:      int   = 0
    tool_calls:    int   = 0
    cost_usd:      float = 0.0
    compacted:     bool  = False
    output_total:  int   = 0
    error:         str   = ""
    extra:         dict  = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Claude Code / Claude Code Desktop
# ─────────────────────────────────────────────────────────────────────────────

def find_cc_session() -> Path | None:
    """Most-recently-modified *.jsonl under ~/.claude/projects/."""
    base = Path.home() / ".claude" / "projects"
    if not base.exists():
        return None
    files = list(base.rglob("*.jsonl"))
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def parse_cc(path: Path | None = None) -> SessionData:
    """Parse a Claude Code JSONL session file."""
    data = SessionData(agent="Claude Code")

    if path is None:
        path = find_cc_session()
    if path is None or not path.exists():
        data.error = "No CC session found. Start Claude Code first."
        return data

    data.session_file = path.name
    latest_usage: dict = {}
    total_cost = 0.0

    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg = entry.get("message", {})
                if msg.get("role") == "assistant" and "usage" in msg:
                    u = msg["usage"]
                    latest_usage = u
                    data.model = msg.get("model", data.model)
                    data.messages += 1
                    data.output_total += u.get("output_tokens", 0)

                    p = PRICING["claude"]
                    total_cost += (u.get("input_tokens", 0)                / 1e6) * p["input"]
                    total_cost += (u.get("cache_creation_input_tokens", 0) / 1e6) * p["cache_creation"]
                    total_cost += (u.get("cache_read_input_tokens", 0)     / 1e6) * p["cache_read"]
                    total_cost += (u.get("output_tokens", 0)               / 1e6) * p["output"]

                if entry.get("type") in ("tool_use", "create") or (
                    isinstance(msg.get("content"), list)
                    and any(c.get("type") == "tool_use" for c in msg.get("content", []))
                ):
                    data.tool_calls += 1

                if entry.get("type") == "system" and "compact" in str(entry).lower():
                    data.compacted = True

    except (IOError, OSError) as e:
        data.error = str(e)
        return data

    data.input_tokens  = latest_usage.get("input_tokens", 0)
    data.output_tokens = latest_usage.get("output_tokens", 0)
    data.cache_read    = latest_usage.get("cache_read_input_tokens", 0)
    data.cache_write   = latest_usage.get("cache_creation_input_tokens", 0)
    data.cost_usd      = total_cost
    data.total_context = data.input_tokens + data.cache_read + data.cache_write
    data.context_limit = MODEL_LIMITS.get(data.model, DEFAULT_LIMIT)
    data.context_pct   = min(100.0, data.total_context / data.context_limit * 100)
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Hermes Agent
# ─────────────────────────────────────────────────────────────────────────────

def find_hermes_db() -> Path | None:
    return Path.home() / ".hermes" / "state.db"


def parse_hermes(session_id: str | None = None) -> SessionData:
    """Read latest (or specified) session from Hermes state.db."""
    data = SessionData(agent="Hermes")

    db_path = find_hermes_db()
    if db_path is None or not db_path.exists():
        data.error = "Hermes state.db not found. Is Hermes installed?"
        return data

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        if session_id:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM sessions ORDER BY started_at DESC LIMIT 1"
            ).fetchone()

        if not row:
            data.error = "No Hermes sessions found."
            conn.close()
            return data

        data.session_file  = row["id"]
        data.model         = row["model"] or "claude-sonnet-4-6"
        data.messages      = row["message_count"] or 0
        data.tool_calls    = row["tool_call_count"] or 0
        data.input_tokens  = row["input_tokens"] or 0
        data.output_tokens = row["output_tokens"] or 0
        data.cache_read    = row["cache_read_tokens"] or 0
        data.cache_write   = row["cache_write_tokens"] or 0
        data.cost_usd      = row["estimated_cost_usd"] or 0.0
        data.extra["actual_cost_usd"]  = row["actual_cost_usd"]
        data.extra["reasoning_tokens"] = row["reasoning_tokens"] or 0
        data.extra["title"]            = row["title"] or ""

        data.total_context = data.input_tokens + data.cache_read + data.cache_write
        data.context_limit = MODEL_LIMITS.get(data.model, DEFAULT_LIMIT)
        data.context_pct   = min(100.0, data.total_context / data.context_limit * 100)
        # output_total for velocity calc
        data.output_total  = data.output_tokens

        conn.close()

    except (sqlite3.Error, KeyError) as e:
        data.error = f"Hermes DB error: {e}"

    return data


# ─────────────────────────────────────────────────────────────────────────────
# Gemini CLI  (limited — history files are permission-restricted on Windows)
# ─────────────────────────────────────────────────────────────────────────────

def parse_gemini() -> SessionData:
    data = SessionData(agent="Gemini CLI")
    history_dir = Path.home() / ".gemini" / "history"

    if not history_dir.exists():
        data.error = "Gemini history not found. Is Gemini CLI installed?"
        return data

    files = sorted(history_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        data.error = "No Gemini history files found."
        return data

    try:
        raw = files[0].read_text(encoding="utf-8", errors="ignore")
        entry = json.loads(raw)
        usage = entry.get("usageMetadata", {})
        data.session_file  = files[0].name[:16]
        data.model         = entry.get("model", "gemini-2.0-flash")
        data.input_tokens  = usage.get("promptTokenCount", 0)
        data.output_tokens = usage.get("candidatesTokenCount", 0)
        data.messages      = entry.get("turnCount", 0)
        data.total_context = data.input_tokens
        data.context_limit = MODEL_LIMITS.get(data.model, 1_000_000)
        data.context_pct   = min(100.0, data.total_context / data.context_limit * 100)

        p = PRICING["gemini"]
        data.cost_usd = (
            (data.input_tokens  / 1e6) * p["input"] +
            (data.output_tokens / 1e6) * p["output"]
        )
        data.output_total = data.output_tokens

    except PermissionError:
        data.error = "Gemini history files are permission-restricted on this system."
    except (json.JSONDecodeError, OSError, KeyError) as e:
        data.error = f"Gemini parse error: {e}"

    return data


# ─────────────────────────────────────────────────────────────────────────────
# Claw Code  (ultraworkers/claw-code — open-source Rust Claude Code parity)
# Session path: ~/.claw/sessions/**/*.jsonl  OR  ./.claw/sessions/**/*.jsonl
# JSONL format mirrors CC exactly: same usage fields per assistant message.
# ─────────────────────────────────────────────────────────────────────────────

def find_claw_session() -> Path | None:
    """Most-recently-modified *.jsonl under ~/.claw/sessions/ or ./.claw/sessions/."""
    candidates: list[Path] = []
    for base in (Path.home() / ".claw" / "sessions", Path(".claw") / "sessions"):
        if base.exists():
            candidates.extend(base.rglob("*.jsonl"))
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def parse_claw(path: Path | None = None) -> SessionData:
    """Parse a Claw Code JSONL session file (same format as Claude Code)."""
    data = SessionData(agent="Claw Code")

    if path is None:
        path = find_claw_session()
    if path is None or not path.exists():
        data.error = "No Claw Code session found. Run `claw` first."
        return data

    data.session_file = path.name
    latest_usage: dict = {}
    total_cost = 0.0

    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg = entry.get("message", {})
                if msg.get("role") == "assistant" and "usage" in msg:
                    u = msg["usage"]
                    latest_usage = u
                    data.model = msg.get("model", data.model)
                    data.messages += 1
                    data.output_total += u.get("output_tokens", 0)

                    p = PRICING["claude"]
                    total_cost += (u.get("input_tokens", 0)                / 1e6) * p["input"]
                    total_cost += (u.get("cache_creation_input_tokens", 0) / 1e6) * p["cache_creation"]
                    total_cost += (u.get("cache_read_input_tokens", 0)     / 1e6) * p["cache_read"]
                    total_cost += (u.get("output_tokens", 0)               / 1e6) * p["output"]

                if isinstance(msg.get("content"), list) and any(
                    c.get("type") == "tool_use" for c in msg.get("content", [])
                ):
                    data.tool_calls += 1

    except (IOError, OSError) as e:
        data.error = str(e)
        return data

    data.input_tokens  = latest_usage.get("input_tokens", 0)
    data.output_tokens = latest_usage.get("output_tokens", 0)
    data.cache_read    = latest_usage.get("cache_read_input_tokens", 0)
    data.cache_write   = latest_usage.get("cache_creation_input_tokens", 0)
    data.cost_usd      = total_cost
    data.total_context = data.input_tokens + data.cache_read + data.cache_write
    data.context_limit = MODEL_LIMITS.get(data.model, DEFAULT_LIMIT)
    data.context_pct   = min(100.0, data.total_context / data.context_limit * 100)
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Goose  (placeholder — session format not yet available)
# ─────────────────────────────────────────────────────────────────────────────

def parse_goose() -> SessionData:
    data = SessionData(agent="Goose")
    data.error = "Goose support coming soon."
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Auto-detect
# ─────────────────────────────────────────────────────────────────────────────

AGENTS = {
    "cc":      parse_cc,
    "claude":  parse_cc,
    "desktop": parse_cc,
    "hermes":  parse_hermes,
    "claw":    parse_claw,
    "gemini":  parse_gemini,
    "goose":   parse_goose,
}


def parse_agent(agent: str = "cc", **kwargs) -> SessionData:
    fn = AGENTS.get(agent.lower())
    if fn is None:
        d = SessionData()
        d.error = f"Unknown agent '{agent}'. Choose: {', '.join(AGENTS)}"
        return d
    return fn(**kwargs)
