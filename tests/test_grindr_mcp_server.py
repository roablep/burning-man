import json

from bm.grindr_mcp_server import GrindrApiClient, GrindrMcpServer


class StubClient(GrindrApiClient):
    def __init__(self):
        super().__init__(base_url="https://example.com")
        self.calls = []

    def _request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return {"ok": True, "method": method, "path": path, "kwargs": kwargs}


def test_tools_list_includes_expected_tools():
    server = GrindrMcpServer(StubClient())
    response = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    tools = response["result"]["tools"]
    names = {tool["name"] for tool in tools}
    assert {"bootstrap", "managed_fields", "create_session", "nearby_profiles", "profiles", "api_request"}.issubset(names)


def test_nearby_profiles_dispatches_to_expected_endpoint():
    client = StubClient()
    server = GrindrMcpServer(client)

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "nearby_profiles",
            "arguments": {"sessionId": "sess", "geohash": "abc", "pageNumber": 2},
        },
    }

    response = server.handle_request(request)
    assert "result" in response

    method, path, kwargs = client.calls[0]
    assert method == "GET"
    assert path == "/v3/locations/abc/profiles"
    assert kwargs["session_id"] == "sess"
    assert kwargs["query"]["pageNumber"] == 2


def test_create_session_requires_password_or_auth_token():
    server = GrindrMcpServer(StubClient())

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "create_session",
            "arguments": {"email": "user@example.com", "token": "push-token"},
        },
    }

    response = server.handle_request(request)
    assert response["error"]["code"] == -32000
    assert "password or authToken" in response["error"]["message"]


def test_api_request_forwards_method_path_and_payload():
    client = StubClient()
    server = GrindrMcpServer(client)

    request = {
        "jsonrpc": "2.0",
        "id": 22,
        "method": "tools/call",
        "params": {
            "name": "api_request",
            "arguments": {
                "method": "POST",
                "path": "/v3/profiles",
                "sessionId": "sess",
                "jsonBody": {"targetProfileIds": ["1"]},
            },
        },
    }

    response = server.handle_request(request)
    assert "result" in response

    _, _, kwargs = client.calls[0]
    assert kwargs["session_id"] == "sess"
    assert kwargs["json_body"] == {"targetProfileIds": ["1"]}

    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["ok"] is True
