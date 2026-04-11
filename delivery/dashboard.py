#!/usr/bin/env python3
"""
dashboard.py — AI Token Dashboard
Live visual dashboard. Runs in a second terminal alongside your AI agent.

Usage:
  python dashboard.py                    # auto-detects Claude Code session
  python dashboard.py --agent hermes     # Hermes Agent
  python dashboard.py --agent gemini     # Gemini CLI
  python dashboard.py --agent cc         # Claude Code (explicit)
  python dashboard.py --once             # print once and exit
  python dashboard.py --all              # show all agents side by side

Supported agents: cc, hermes, gemini, goose
"""

import os
import sys
import time
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import parse_agent, render, AGENTS

REFRESH_SECS = 5

AGENT_LABELS = {
    "cc":      "Claude Code",
    "claude":  "Claude Code",
    "desktop": "Claude Code Desktop",
    "hermes":  "Hermes",
    "claw":    "Claw Code",
    "gemini":  "Gemini CLI",
    "goose":   "Goose",
}


def print_dashboard(agent: str) -> None:
    data = parse_agent(agent)
    os.system("cls" if os.name == "nt" else "clear")
    print(render(data))
    print(f"\n  {chr(27)}[2mRefreshes every {REFRESH_SECS}s  •  Ctrl+C to exit  •  agent: {agent}{chr(27)}[0m")


def print_all() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    for agent in ["cc", "hermes", "claw", "gemini"]:
        data = parse_agent(agent)
        print(render(data))
        print()
    print(f"  \033[2mRefreshes every {REFRESH_SECS}s  •  Ctrl+C to exit\033[0m")


def main() -> None:
    args = sys.argv[1:]
    once = "--once" in args
    show_all = "--all" in args
    args = [a for a in args if not a.startswith("--")]

    # --agent hermes  or  positional: dashboard.py hermes
    agent = "cc"
    for i, a in enumerate(args):
        if a == "--agent" and i + 1 < len(args):
            agent = args[i + 1]
            break
        elif a in AGENTS:
            agent = a
            break

    if show_all:
        if once:
            print_all()
            return
        try:
            while True:
                print_all()
                time.sleep(REFRESH_SECS)
        except KeyboardInterrupt:
            print("\nDashboard closed.")
        return

    if once:
        data = parse_agent(agent)
        print(render(data))
        return

    print(f"Watching: {AGENT_LABELS.get(agent, agent)}\n")
    time.sleep(0.5)

    try:
        while True:
            print_dashboard(agent)
            time.sleep(REFRESH_SECS)
    except KeyboardInterrupt:
        print("\nDashboard closed.")


if __name__ == "__main__":
    main()
