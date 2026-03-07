"""MCP server exposing an unofficial Grindr v3 REST API wrapper.

This server implements a small subset of the MCP protocol over stdio using
LSP-style framing ("Content-Length" headers + JSON payload).

Environment variables:
    GRINDR_BASE_URL: Optional API base URL (default: https://grindr.mobi)
    GRINDR_USER_AGENT: Optional User-Agent override.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request

DEFAULT_BASE_URL = "https://grindr.mobi"
DEFAULT_USER_AGENT = "grindr3/3.0.1.4529;4529;Unknown;Android 4.4.4"


class GrindrApiError(RuntimeError):
    """Raised when Grindr REST API calls fail."""


@dataclass
class GrindrApiClient:
    """Simple REST client for unofficial Grindr v3 endpoints."""

    base_url: str = DEFAULT_BASE_URL
    user_agent: str = DEFAULT_USER_AGENT

    def _request(
        self,
        method: str,
        path: str,
        *,
        session_id: str | None = None,
        query: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        data: bytes | None = None,
        content_type: str | None = None,
        host_override: str | None = None,
    ) -> dict[str, Any]:
        base_url = host_override or self.base_url
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

        if query:
            query_params = {k: v for k, v in query.items() if v is not None}
            url = f"{url}?{parse.urlencode(query_params)}"

        body: bytes | None = data
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            content_type = "application/json"

        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        if session_id:
            headers["Authorization"] = f"Grindr3 {session_id}"
        if content_type:
            headers["Content-Type"] = content_type

        req = request.Request(url, data=body, headers=headers, method=method.upper())

        try:
            with request.urlopen(req) as response:
                raw = response.read()
                if not raw:
                    return {}
                return json.loads(raw.decode("utf-8"))
        except error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            raise GrindrApiError(
                f"HTTP {exc.code} for {method.upper()} {url}: {payload}"
            ) from exc
        except error.URLError as exc:
            raise GrindrApiError(f"Network error for {method.upper()} {url}: {exc}") from exc


class GrindrMcpServer:
    """Tiny MCP JSON-RPC server exposing Grindr tools."""

    def __init__(self, client: GrindrApiClient) -> None:
        self.client = client

    @staticmethod
    def _tool_definitions() -> list[dict[str, Any]]:
        return [
            {
                "name": "bootstrap",
                "description": "Fetch dynamic service/config bootstrap data from /v3/bootstrap.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "managed_fields",
                "description": "Fetch managed enum fields from /v3/managed-fields.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "create_session",
                "description": "Create session via email+password or email+authToken.",
                "inputSchema": {
                    "type": "object",
                    "required": ["email", "token"],
                    "properties": {
                        "email": {"type": "string"},
                        "token": {"type": "string", "description": "Push token (GCM/FCM)."},
                        "password": {"type": "string"},
                        "authToken": {"type": "string"},
                    },
                },
            },
            {
                "name": "nearby_profiles",
                "description": "Get nearby profiles for a geohash.",
                "inputSchema": {
                    "type": "object",
                    "required": ["sessionId", "geohash"],
                    "properties": {
                        "sessionId": {"type": "string"},
                        "geohash": {"type": "string"},
                        "online": {"type": "boolean"},
                        "photoOnly": {"type": "boolean"},
                        "favorite": {"type": "boolean"},
                        "pageNumber": {"type": "integer"},
                    },
                },
            },
            {
                "name": "profiles",
                "description": "Get details for one or more target profile IDs.",
                "inputSchema": {
                    "type": "object",
                    "required": ["sessionId"],
                    "properties": {
                        "sessionId": {"type": "string"},
                        "targetProfileIds": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "profileId": {"type": "string"},
                    },
                },
            },
            {
                "name": "me_prefs",
                "description": "Get current user preferences.",
                "inputSchema": {
                    "type": "object",
                    "required": ["sessionId"],
                    "properties": {"sessionId": {"type": "string"}},
                },
            },
            {
                "name": "system_messages",
                "description": "Get moderation/system messages.",
                "inputSchema": {
                    "type": "object",
                    "required": ["sessionId"],
                    "properties": {"sessionId": {"type": "string"}},
                },
            },
            {
                "name": "api_request",
                "description": "Low-level authenticated/unauthenticated API request helper.",
                "inputSchema": {
                    "type": "object",
                    "required": ["method", "path"],
                    "properties": {
                        "method": {"type": "string"},
                        "path": {"type": "string"},
                        "sessionId": {"type": "string"},
                        "query": {"type": "object"},
                        "jsonBody": {"type": "object"},
                    },
                },
            },
        ]

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "bootstrap":
            result = self.client._request("GET", "/v3/bootstrap")
        elif name == "managed_fields":
            result = self.client._request("GET", "/v3/managed-fields")
        elif name == "create_session":
            payload: dict[str, Any] = {
                "email": arguments["email"],
                "token": arguments["token"],
            }
            if arguments.get("password"):
                payload["password"] = arguments["password"]
            if arguments.get("authToken"):
                payload["authToken"] = arguments["authToken"]
            if "password" not in payload and "authToken" not in payload:
                raise GrindrApiError("create_session requires either password or authToken")
            result = self.client._request("POST", "/v3/sessions", json_body=payload)
        elif name == "nearby_profiles":
            query = {
                "online": arguments.get("online", False),
                "photoOnly": arguments.get("photoOnly", False),
                "favorite": arguments.get("favorite", False),
                "pageNumber": arguments.get("pageNumber", 1),
            }
            result = self.client._request(
                "GET",
                f"/v3/locations/{arguments['geohash']}/profiles",
                session_id=arguments["sessionId"],
                query=query,
            )
        elif name == "profiles":
            if arguments.get("profileId"):
                result = self.client._request(
                    "GET",
                    f"/v3/profiles/{arguments['profileId']}",
                    session_id=arguments["sessionId"],
                )
            else:
                result = self.client._request(
                    "POST",
                    "/v3/profiles",
                    session_id=arguments["sessionId"],
                    json_body={"targetProfileIds": arguments.get("targetProfileIds", [])},
                )
        elif name == "me_prefs":
            result = self.client._request(
                "GET", "/v3/me/prefs", session_id=arguments["sessionId"]
            )
        elif name == "system_messages":
            result = self.client._request(
                "GET", "/v3/systemMessages", session_id=arguments["sessionId"]
            )
        elif name == "api_request":
            result = self.client._request(
                arguments["method"],
                arguments["path"],
                session_id=arguments.get("sessionId"),
                query=arguments.get("query"),
                json_body=arguments.get("jsonBody"),
            )
        else:
            raise GrindrApiError(f"Unknown tool: {name}")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2, sort_keys=True),
                }
            ]
        }

    def handle_request(self, request_obj: dict[str, Any]) -> dict[str, Any] | None:
        method = request_obj.get("method")
        request_id = request_obj.get("id")
        params = request_obj.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "grindr-mcp", "version": "0.1.0"},
                    "capabilities": {"tools": {}},
                },
            }

        if method == "notifications/initialized":
            return None

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": self._tool_definitions()},
            }

        if method == "tools/call":
            try:
                result = self._call_tool(params["name"], params.get("arguments", {}))
                return {"jsonrpc": "2.0", "id": request_id, "result": result}
            except Exception as exc:  # noqa: BLE001
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32000, "message": str(exc)},
                }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def _read_message(stdin: Any) -> dict[str, Any] | None:
    content_length: int | None = None

    while True:
        line = stdin.buffer.readline()
        if not line:
            return None
        decoded = line.decode("utf-8").strip()
        if not decoded:
            break
        if decoded.lower().startswith("content-length:"):
            content_length = int(decoded.split(":", 1)[1].strip())

    if content_length is None:
        raise RuntimeError("Missing Content-Length header")

    payload = stdin.buffer.read(content_length)
    if not payload:
        return None

    return json.loads(payload.decode("utf-8"))


def _write_message(stdout: Any, message: dict[str, Any]) -> None:
    data = json.dumps(message).encode("utf-8")
    stdout.buffer.write(f"Content-Length: {len(data)}\r\n\r\n".encode("utf-8"))
    stdout.buffer.write(data)
    stdout.buffer.flush()


def run_server() -> None:
    client = GrindrApiClient(
        base_url=os.getenv("GRINDR_BASE_URL", DEFAULT_BASE_URL),
        user_agent=os.getenv("GRINDR_USER_AGENT", DEFAULT_USER_AGENT),
    )
    server = GrindrMcpServer(client)

    while True:
        message = _read_message(sys.stdin)
        if message is None:
            break
        response = server.handle_request(message)
        if response is not None:
            _write_message(sys.stdout, response)


if __name__ == "__main__":
    run_server()
