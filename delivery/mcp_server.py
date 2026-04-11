#!/usr/bin/env python3
"""
mcp_server.py — AI Token Dashboard MCP Server
Exposes token data as MCP tools that any MCP-compatible AI agent can call.

Start the server:
  python mcp_server.py

Then in your CLAUDE.md / agent config, point to this server.
Any agent that supports MCP can call:
  - get_token_status   → context %, cost, degradation risk
  - get_token_detail   → full breakdown for one agent
  - get_all_agents     → snapshot of all supported agents

Requirements:
  pip install mcp
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import parse_agent, AGENTS

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


def _status_dict(agent: str) -> dict:
    """Return a compact status dict for one agent."""
    data = parse_agent(agent)
    if data.error:
        return {"agent": data.agent, "error": data.error}

    cache_all = data.cache_read + data.cache_write
    cache_eff = round(data.cache_read / cache_all * 100, 1) if cache_all else 0.0

    risk = "HIGH" if (data.context_pct >= 80 or data.messages >= 30) else \
           "MEDIUM" if (data.context_pct >= 50 or data.messages >= 20) else "LOW"

    result = {
        "agent":          data.agent,
        "model":          data.model,
        "context_pct":    round(data.context_pct, 1),
        "context_used":   data.total_context,
        "context_limit":  data.context_limit,
        "messages":       data.messages,
        "cost_usd":       round(data.cost_usd, 4),
        "cache_efficiency_pct": cache_eff,
        "degradation_risk": risk,
        "compacted":      data.compacted,
        "advice": (
            "Run /compact immediately — context critical" if data.context_pct >= 80
            else "Plan to /compact before message 30 or 80% context" if data.messages >= 25 or data.context_pct >= 55
            else "Session healthy"
        ),
    }
    if data.extra:
        result["extra"] = data.extra
    return result


def _detail_dict(agent: str) -> dict:
    """Return full token breakdown for one agent."""
    data = parse_agent(agent)
    if data.error:
        return {"agent": data.agent, "error": data.error}
    return {
        "agent":          data.agent,
        "model":          data.model,
        "session":        data.session_file,
        "input_tokens":   data.input_tokens,
        "output_tokens":  data.output_tokens,
        "cache_read":     data.cache_read,
        "cache_write":    data.cache_write,
        "total_context":  data.total_context,
        "context_limit":  data.context_limit,
        "context_pct":    round(data.context_pct, 2),
        "messages":       data.messages,
        "tool_calls":     data.tool_calls,
        "cost_usd":       round(data.cost_usd, 6),
        "compacted":      data.compacted,
        "extra":          data.extra,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: run as HTTP JSON API if MCP package not installed
# ─────────────────────────────────────────────────────────────────────────────

def run_http_fallback(port: int = 7421) -> None:
    """Simple HTTP JSON API — fallback when mcp package is not installed."""
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse, parse_qs

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # silence request logs

        def do_GET(self):
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            agent = qs.get("agent", ["cc"])[0]

            if parsed.path == "/status":
                body = _status_dict(agent)
            elif parsed.path == "/detail":
                body = _detail_dict(agent)
            elif parsed.path == "/all":
                body = {a: _status_dict(a) for a in ["cc", "hermes", "gemini"]}
            elif parsed.path == "/health":
                body = {"status": "ok", "mode": "http-fallback"}
            else:
                body = {"error": f"Unknown path {parsed.path}. Try /status, /detail, /all"}

            payload = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(payload))
            self.end_headers()
            self.wfile.write(payload)

    print(f"AI Token Dashboard — HTTP fallback mode (MCP package not installed)")
    print(f"Listening on http://localhost:{port}")
    print(f"  GET /status?agent=cc|hermes|gemini")
    print(f"  GET /detail?agent=cc|hermes|gemini")
    print(f"  GET /all")
    print(f"Ctrl+C to stop")
    HTTPServer(("", port), Handler).serve_forever()


# ─────────────────────────────────────────────────────────────────────────────
# MCP Server
# ─────────────────────────────────────────────────────────────────────────────

def run_mcp() -> None:
    server = Server("ai-token-dashboard")

    @server.list_tools()
    async def list_tools():
        return [
            types.Tool(
                name="get_token_status",
                description=(
                    "Get current token usage status for an AI agent. "
                    "Returns context %, cost, degradation risk, and advice. "
                    "Use this to decide whether to /compact or switch models."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent": {
                            "type": "string",
                            "enum": ["cc", "hermes", "gemini", "all"],
                            "default": "cc",
                            "description": "Which agent to check",
                        }
                    },
                },
            ),
            types.Tool(
                name="get_token_detail",
                description=(
                    "Get full token breakdown for an AI agent — "
                    "input, output, cache read/write, total context, cost."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent": {
                            "type": "string",
                            "enum": ["cc", "hermes", "gemini"],
                            "default": "cc",
                        }
                    },
                },
            ),
            types.Tool(
                name="get_all_agents",
                description="Get token status snapshot for all supported agents at once.",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "get_token_status":
            agent = arguments.get("agent", "cc")
            if agent == "all":
                result = {a: _status_dict(a) for a in ["cc", "hermes", "gemini"]}
            else:
                result = _status_dict(agent)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        if name == "get_token_detail":
            agent = arguments.get("agent", "cc")
            return [types.TextContent(type="text", text=json.dumps(_detail_dict(agent), indent=2))]

        if name == "get_all_agents":
            result = {a: _status_dict(a) for a in ["cc", "hermes", "gemini"]}
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    import asyncio

    async def main():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(main())


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = 7421
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--port" and i + 1 < len(sys.argv) - 1:
            port = int(sys.argv[i + 2])
        if arg == "--http":
            run_http_fallback(port)
            sys.exit(0)

    if MCP_AVAILABLE:
        run_mcp()
    else:
        print("MCP package not found — falling back to HTTP mode.")
        print("Install MCP: pip install mcp")
        print()
        run_http_fallback(port)
