#!/usr/bin/env python3
"""
cli.py — AI Token Dashboard CLI
One-shot token snapshot from the command line.

Usage:
  python cli.py                      # Claude Code, single snapshot
  python cli.py --agent hermes       # Hermes Agent
  python cli.py --agent gemini       # Gemini CLI
  python cli.py --agent cc           # Claude Code (explicit)
  python cli.py --agent all          # all agents

Install as a command (optional):
  pip install -e .   (after setup.py is added)
  gauge --agent hermes
"""

import argparse
import sys
import io
from pathlib import Path

# Force UTF-8 output on Windows so box-drawing characters render correctly
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import parse_agent, render, AGENTS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gauge",
        description="AI Token Dashboard — instant token snapshot for any AI agent.",
    )
    parser.add_argument(
        "--agent", "-a",
        default="cc",
        choices=list(AGENTS.keys()) + ["all"],
        help="Which agent to read (default: cc)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of visual dashboard",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Print once and exit (same as default CLI behaviour — kept for compatibility)",
    )
    args = parser.parse_args()

    if args.agent == "all":
        targets = ["cc", "hermes", "claw", "gemini"]
    else:
        targets = [args.agent]

    for agent in targets:
        data = parse_agent(agent)

        if args.json:
            import json
            out = {
                "agent":         data.agent,
                "model":         data.model,
                "context_pct":   round(data.context_pct, 2),
                "input_tokens":  data.input_tokens,
                "output_tokens": data.output_tokens,
                "cache_read":    data.cache_read,
                "cache_write":   data.cache_write,
                "total_context": data.total_context,
                "context_limit": data.context_limit,
                "messages":      data.messages,
                "tool_calls":    data.tool_calls,
                "cost_usd":      round(data.cost_usd, 6),
                "compacted":     data.compacted,
                "error":         data.error or None,
            }
            if data.extra:
                out["extra"] = data.extra
            print(json.dumps(out))
        else:
            print(render(data))
            if len(targets) > 1:
                print()


if __name__ == "__main__":
    main()
