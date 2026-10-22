#!/usr/bin/env python3
"""DeepSeek Search/Fetch as an MCP stdio server. Python 3 stdlib only.

One JSON-RPC message per line on stdin/stdout. Only protocol traffic goes to
stdout. API responses are returned verbatim as JSON text; tool definitions live
in tools.json next to this file.
"""

import http.client
import io
import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com").rstrip("/")
NAME, VERSION, PROTOCOL = "deepseek-search", "0.2.0", "2024-11-05"
TIMEOUT = 45

TOOLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools.json")


class ToolError(Exception):
    """Only the code crosses into the model's context; meaning lives in the tool description."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def reply(rid, result=None, error=None):
    """Write one JSON-RPC response. Never call this for notifications."""
    msg = {"jsonrpc": "2.0", "id": rid}
    if error:
        msg["error"] = {"code": error[0], "message": error[1]}
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def api(path, payload):
    """POST to the DeepSeek API and return the body verbatim."""
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise ToolError("auth_failed")

    request = urllib.request.Request(
        API_BASE + path,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        method="POST",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise ToolError("auth_failed")
        if exc.code == 402:
            raise ToolError("insufficient_balance")
        if exc.code == 429:
            raise ToolError("rate_limited")
        if exc.code >= 500:
            raise ToolError("service_error")
        raise ToolError("invalid_request")
    except (urllib.error.URLError, OSError, http.client.HTTPException):
        raise ToolError("network_error")


def web_search(arguments):
    """Forward a search request; the API's JSON is the answer."""
    return api("/v1/tools/search", arguments)


def web_fetch(arguments):
    """Forward a fetch request; the API's JSON is the answer."""
    return api("/v1/tools/fetch", arguments)


# Tool names are function names, so dispatch is a plain globals() lookup.
# The set of legal names comes from tools.json, never from the request.
def load_tools():
    """Read tool definitions once at startup. A broken file must fail loudly."""
    with open(TOOLS_FILE, encoding="utf-8") as handle:
        return json.load(handle)["tools"]


def call_tool(name, arguments, tool_names):
    """Dispatch a tools/call request, turning failures into tool-level errors."""
    try:
        if name not in tool_names:
            raise ToolError("invalid_request")
        return {"content": [{"type": "text", "text": globals()[name](arguments)}]}
    except ToolError as exc:
        return {"content": [{"type": "text", "text": exc.code}], "isError": True}
    except Exception as exc:  # noqa: BLE001 - internal_error is part of the documented contract
        print(f"deepseek-search bug: {exc!r}", file=sys.stderr, flush=True)
        return {
            "content": [{"type": "text", "text": "internal_error"}],
            "isError": True,
        }


def handle(request, tools):
    """Answer one decoded JSON-RPC request. Notifications are ignored."""
    rid = request.get("id")
    if rid is None:  # notification: never reply
        return

    method = request.get("method") or ""

    if method == "initialize":
        result = {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": NAME, "version": VERSION},
        }
    elif method == "tools/list":
        result = {"tools": tools}
    elif method == "tools/call":
        params = request.get("params") or {}
        names = {tool["name"] for tool in tools}
        result = call_tool(
            params.get("name") or "", params.get("arguments") or {}, names
        )
    elif method == "ping":
        result = {}
    elif method == "resources/list":
        result = {"resources": []}
    elif method == "prompts/list":
        result = {"prompts": []}
    else:
        return reply(rid, error=(-32601, f"Method not found: {method}"))

    reply(rid, result)


def serve(tools):
    """Read newline-delimited JSON-RPC from stdin until EOF."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except ValueError:
            reply(None, error=(-32700, "Parse error"))
            continue

        for item in payload if isinstance(payload, list) else [payload]:
            try:
                handle(item, tools)
            except Exception as exc:  # noqa: BLE001 - one bad request must not kill the server
                print(
                    f"deepseek-search dispatch error: {exc!r}",
                    file=sys.stderr,
                    flush=True,
                )
                if item.get("id") is not None:
                    reply(item["id"], error=(-32603, "Internal error"))


def main():
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        # reconfigure only exists on TextIOWrapper; hosts may substitute other streams.
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    serve(load_tools())


if __name__ == "__main__":
    main()
