"""
renderer.py — AI Token Dashboard
Renders the visual dashboard from SessionData.
"""

import re
from .parser import SessionData

# ── ANSI colours ──────────────────────────────────────────────────────────────
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

W = 54  # inner box width


def _strip(s: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", s)


def _bar(pct: float, width: int = 22) -> str:
    filled = max(0, min(round(pct / 100 * width), width))
    b = "█" * filled + "░" * (width - filled)
    if pct >= 80:   colour = RED
    elif pct >= 50: colour = YELLOW
    else:           colour = GREEN
    return f"{colour}{b}{RESET}"


def _row(label: str, gauge: str, detail: str) -> str:
    content = f"  {label:<10} {gauge}  {detail}"
    pad = W - len(_strip(content)) + 2
    return f"║{content}{' ' * max(pad, 0)}║"


def _info(text: str) -> str:
    pad = W - len(_strip(text)) + 2
    return f"║  {text}{' ' * max(pad - 2, 0)}║"


def _div() -> str:
    return f"╠{'═' * W}╣"


def _risk(messages: int, ctx_pct: float) -> tuple[str, str]:
    if ctx_pct >= 80 or messages >= 30:
        return "HIGH  ⚠", RED
    if ctx_pct >= 50 or messages >= 20:
        return "MEDIUM", YELLOW
    return "LOW   ✓", GREEN


def render(data: SessionData) -> str:
    if data.error:
        return (
            f"╔{'═' * W}╗\n"
            f"║  {BOLD}{data.agent} — Error{RESET}{' ' * (W - len(data.agent) - 10)}║\n"
            f"║  {RED}{data.error}{RESET}{' ' * max(W - len(data.error) - 2, 0)}║\n"
            f"╚{'═' * W}╝"
        )

    ctx_pct   = data.context_pct
    cost      = data.cost_usd
    msgs      = data.messages
    velocity  = data.output_total / max(msgs, 1)

    cached_all = data.cache_read + data.cache_write
    cache_eff  = (data.cache_read / cached_all * 100) if cached_all else 0.0

    risk, rc = _risk(msgs, ctx_pct)

    if ctx_pct >= 80:   ctx_tag = f"{RED}⚠  compact NOW{RESET}"
    elif ctx_pct >= 50: ctx_tag = f"{YELLOW}⚡ compact soon{RESET}"
    else:               ctx_tag = f"{GREEN}✓  healthy{RESET}"

    agent_label = f"{BOLD}{data.agent}{RESET}"
    model_label = f"{DIM}{data.model}{RESET}"

    lines = [
        f"╔{'═' * W}╗",
        _info(f"{agent_label}  {model_label}"),
        _info(f"{DIM}session: {data.session_file[:42]}{RESET}"),
        _div(),
        _row("CONTEXT",  _bar(ctx_pct),                    f"{ctx_pct:5.1f}%  {ctx_tag}"),
        _row("COST",     _bar(min(cost / 5.0 * 100, 100)), f"${cost:.4f}  {DIM}(est, $5=full){RESET}"),
        _row("MESSAGES", _bar(msgs / 50 * 100),            f"{msgs:3d}  {DIM}(30+ = risk){RESET}"),
        _row("VELOCITY", _bar(velocity / 2000 * 100),      f"{velocity:,.0f} tok/msg"),
        _div(),
        _info(f"{BOLD}TOKEN BREAKDOWN{RESET}"),
        _info(f"  Input (fresh):   {data.input_tokens:>10,}   {DIM}@ $3.00/M{RESET}"),
        _info(f"  Cache READ:      {data.cache_read:>10,}   {DIM}@ $0.30/M  ← cheap{RESET}"),
        _info(f"  Cache CREATED:   {data.cache_write:>10,}   {DIM}@ $3.75/M{RESET}"),
        _info(f"  Output:          {data.output_tokens:>10,}   {DIM}@ $15.00/M{RESET}"),
        _info(f"  Total context:   {data.total_context:>10,}   {DIM}/ {data.context_limit:,}{RESET}"),
        _div(),
        _info(f"  Cache efficiency : {cache_eff:5.1f}%   {DIM}(high = lower cost){RESET}"),
        _info(f"  Tool calls       : {data.tool_calls:5d}"),
        _info(f"  Compacted        : {'YES' if data.compacted else 'no'}"),
        _info(f"  Degradation risk : {rc}{risk}{RESET}   {DIM}(Anthropic research){RESET}"),
    ]

    # Hermes extras
    if data.extra.get("reasoning_tokens"):
        lines.append(_info(f"  Reasoning tokens : {data.extra['reasoning_tokens']:>10,}"))
    if data.extra.get("actual_cost_usd"):
        lines.append(_info(f"  Actual cost (API): ${data.extra['actual_cost_usd']:.4f}"))

    lines.append(_div())

    # Advice
    if ctx_pct >= 80:
        advice = f"  {RED}→  compact immediately — context at {ctx_pct:.0f}%{RESET}"
    elif msgs >= 25 or ctx_pct >= 55:
        advice = f"  {YELLOW}→  plan to compact before message 30 / 80% context{RESET}"
    elif cache_eff < 30 and cached_all > 0:
        advice = f"  {YELLOW}→  low cache reuse — compact to rebuild cache{RESET}"
    else:
        advice = f"  {GREEN}→  session healthy — keep going{RESET}"

    lines += [
        f"║{advice}{'':>{W - len(_strip(advice)) + 1}}║",
        f"╚{'═' * W}╝",
    ]

    return "\n".join(lines)
