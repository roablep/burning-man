"""MCP server for the unofficial Grindr v3 API."""

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = "https://grindr.mobi"
UPLOAD_URL = "https://g3-beta-upload.grindr.com"
CDN_URL = "http://cdns.grindr.com"
USER_AGENT = "grindr3/3.0.1.4529;4529;Unknown;Android 4.4.4"

mcp = FastMCP("Grindr")

# In-memory session state (per server process)
_session: dict = {
    "session_id": None,
    "profile_id": None,
    "auth_token": None,
    "email": None,
    "xmpp_token": None,
}


def _headers(authenticated: bool = True) -> dict:
    h = {"User-Agent": USER_AGENT}
    if authenticated:
        if not _session["session_id"]:
            raise ValueError("Not logged in. Call login first.")
        h["Authorization"] = f"Grindr3 {_session['session_id']}"
    return h


# ─── Auth ────────────────────────────────────────────────────────────────────


@mcp.tool()
def login(email: str, password: str | None = None, auth_token: str | None = None) -> dict:
    """Log in to Grindr.

    Provide either `password` (first login) or `auth_token` (subsequent logins).
    Returns profile_id, session_id, and xmpp_token on success.
    Saves credentials in the server session for all subsequent calls.
    """
    payload: dict = {"email": email, "token": "mcp-placeholder-gcm-token"}
    if auth_token:
        payload["authToken"] = auth_token
    elif password:
        payload["password"] = password
    else:
        raise ValueError("Provide either password or auth_token")

    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/v3/sessions",
            json=payload,
            headers=_headers(authenticated=False),
        )
        resp.raise_for_status()
        data = resp.json()

    _session["session_id"] = data.get("sessionId")
    _session["profile_id"] = data.get("profileId")
    _session["xmpp_token"] = data.get("xmppToken")
    _session["email"] = email
    if "authToken" in data:
        _session["auth_token"] = data["authToken"]

    return {
        "profileId": data.get("profileId"),
        "sessionId": data.get("sessionId"),
        "xmppToken": data.get("xmppToken"),
        "authToken": data.get("authToken"),
    }


@mcp.tool()
def logout() -> dict:
    """Clear the current session (local only; does not delete the account)."""
    _session.update(session_id=None, profile_id=None, xmpp_token=None)
    return {"status": "logged out"}


# ─── Bootstrap / Managed fields ──────────────────────────────────────────────


@mcp.tool()
def get_bootstrap() -> dict:
    """Fetch dynamic server configuration and service endpoints from /v3/bootstrap."""
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/v3/bootstrap",
            headers=_headers(authenticated=False),
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def get_managed_fields() -> dict:
    """Fetch managed enum fields: lookingFor, bodyType, ethnicity, grindrTribes, etc."""
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/v3/managed-fields",
            headers=_headers(authenticated=False),
        )
        resp.raise_for_status()
        return resp.json()


# ─── My profile & preferences ────────────────────────────────────────────────


@mcp.tool()
def update_my_profile(
    about_me: str = "",
    age: int = 18,
    display_name: str = "",
    body_type: int = 0,
    ethnicity: int = 0,
    height_cm: float = -1.0,
    weight_g: float = -1.0,
    looking_for: list[int] | None = None,
    relationship_status: int = 0,
    grindr_tribes: list[int] | None = None,
    show_age: bool = False,
    show_distance: bool = False,
) -> dict:
    """Update your public Grindr profile.

    body_type, ethnicity, relationship_status, looking_for, and grindr_tribes
    are managed-field IDs (see get_managed_fields).
    height_cm: centimetres, or -1.0 to hide.
    weight_g: grams, or -1.0 to hide.
    """
    payload = {
        "aboutMe": about_me,
        "age": age,
        "bodyType": body_type,
        "displayName": display_name,
        "ethnicity": ethnicity,
        "grindrTribes": grindr_tribes or [],
        "height": height_cm,
        "lookingFor": looking_for or [],
        "relationshipStatus": relationship_status,
        "showAge": show_age,
        "showDistance": show_distance,
        "socialNetworks": {
            "facebook": {"userId": ""},
            "instagram": {"userId": ""},
            "twitter": {"userId": ""},
        },
        "weight": weight_g,
    }
    with httpx.Client() as client:
        resp = client.put(
            f"{BASE_URL}/v3/me/profile",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json() or {"status": "ok"}


@mcp.tool()
def get_my_prefs() -> dict:
    """Get your account preferences: filters, chat photos, saved phrases, unit system."""
    with httpx.Client() as client:
        resp = client.get(f"{BASE_URL}/v3/me/prefs", headers=_headers())
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def get_system_messages() -> dict:
    """Fetch system messages (e.g. photo approval/rejection notifications)."""
    with httpx.Client() as client:
        resp = client.get(f"{BASE_URL}/v3/systemMessages", headers=_headers())
        resp.raise_for_status()
        return resp.json()


# ─── Nearby profiles ─────────────────────────────────────────────────────────


@mcp.tool()
def get_nearby_profiles(
    geohash: str,
    online_only: bool = False,
    photo_only: bool = False,
    favorites_only: bool = False,
    page_number: int = 1,
) -> dict:
    """Get profiles near a location.

    geohash: a geohash string for the target location (see https://en.wikipedia.org/wiki/Geohash).
    Returns a list of nearby profiles with distance, age, display name, and profile image hash.
    Profile images are available at:
      http://cdns.grindr.com/images/profile/1024x1024/<profileImageMediaHash>
      http://cdns.grindr.com/images/thumb/320x320/<profileImageMediaHash>
    """
    params = {
        "online": str(online_only).lower(),
        "photoOnly": str(photo_only).lower(),
        "favorite": str(favorites_only).lower(),
        "pageNumber": page_number,
    }
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/v3/locations/{geohash}/profiles",
            params=params,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


# ─── Specific profiles ───────────────────────────────────────────────────────


@mcp.tool()
def get_profile(profile_id: str) -> dict:
    """Fetch the public profile for a single user by profile ID."""
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/v3/profiles/{profile_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def get_profiles(profile_ids: list[str]) -> dict:
    """Fetch public profiles for multiple users in one request."""
    payload = {"targetProfileIds": profile_ids}
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/v3/profiles",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


# ─── Favorites ───────────────────────────────────────────────────────────────


@mcp.tool()
def add_favorite(profile_id: str) -> dict:
    """Add a user to your favorites (star them)."""
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/v3/favorites/{profile_id}",
            headers=_headers(),
            content=b"",
        )
        resp.raise_for_status()
        return resp.json() or {"status": "ok"}


@mcp.tool()
def remove_favorite(profile_id: str) -> dict:
    """Remove a user from your favorites."""
    with httpx.Client() as client:
        resp = client.delete(
            f"{BASE_URL}/v3/favorites/{profile_id}",
            headers=_headers(),
            content=b"",
        )
        resp.raise_for_status()
        return resp.json() or {"status": "ok"}


# ─── Blocks ───────────────────────────────────────────────────────────────────


@mcp.tool()
def get_blocks() -> dict:
    """Get the list of users blocking you and users you've blocked."""
    with httpx.Client() as client:
        resp = client.get(f"{BASE_URL}/v3/me/blocks", headers=_headers())
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def block_user(profile_id: str) -> dict:
    """Block a user by profile ID."""
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/v3/blocks/{profile_id}",
            headers=_headers(),
            content=b"",
        )
        resp.raise_for_status()
        return resp.json() or {"status": "ok"}


@mcp.tool()
def unblock_all() -> dict:
    """Unblock all currently blocked users."""
    with httpx.Client() as client:
        resp = client.delete(f"{BASE_URL}/v3/me/blocks", headers=_headers())
        resp.raise_for_status()
        return resp.json() or {"status": "ok"}


# ─── Reporting ───────────────────────────────────────────────────────────────


@mcp.tool()
def report_user(profile_id: str, reason_id: int, comment: str = "") -> dict:
    """Report a user for abuse.

    reason_id: integer from the reportReasons managed field (see get_managed_fields).
    comment: optional free-text note (legacy field, may be ignored by the server).
    """
    payload = {"comment": comment, "reason": reason_id}
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/v3/flags/{profile_id}",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json() or {"status": "ok"}


# ─── Messaging ───────────────────────────────────────────────────────────────


@mcp.tool()
def get_undelivered_messages() -> dict:
    """Fetch messages that were sent while you were offline."""
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/v3/me/chat/messages",
            params={"undelivered": "true"},
            headers=_headers(),
            content=b"",
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def acknowledge_messages(message_ids: list[str]) -> dict:
    """Acknowledge received chat messages by their UUIDs."""
    payload = {"messageIds": message_ids}
    with httpx.Client() as client:
        resp = client.put(
            f"{BASE_URL}/v3/me/chat/messages",
            params={"confirmed": "true"},
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json() or {"status": "ok"}


# ─── Broadcast / ads ─────────────────────────────────────────────────────────


@mcp.tool()
def get_broadcast_messages() -> dict:
    """Fetch targeted broadcast/ad messages from Grindr."""
    with httpx.Client() as client:
        resp = client.get(f"{BASE_URL}/v3/broadcastMessages", headers=_headers())
        resp.raise_for_status()
        return resp.json()


# ─── Account management ──────────────────────────────────────────────────────


@mcp.tool()
def change_password(old_password: str, new_password: str) -> dict:
    """Change your account password. Updates the stored auth token on success."""
    payload = {"oldPassword": old_password, "newPassword": new_password}
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/v3/users/update-password",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    if "authToken" in data:
        _session["auth_token"] = data["authToken"]
    if "sessionId" in data:
        _session["session_id"] = data["sessionId"]

    return data


@mcp.tool()
def change_email(new_email: str, password: str) -> dict:
    """Change the email address on your account."""
    payload = {"newEmail": new_email, "password": password}
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/v3/users/email",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    if "authToken" in data:
        _session["auth_token"] = data["authToken"]
        _session["email"] = new_email
    if "sessionId" in data:
        _session["session_id"] = data["sessionId"]

    return data


@mcp.tool()
def delete_account() -> dict:
    """Permanently delete your Grindr account from the server. This cannot be undone."""
    with httpx.Client() as client:
        resp = client.delete(f"{BASE_URL}/v3/me/profile", headers=_headers())
        resp.raise_for_status()
    _session.update(session_id=None, profile_id=None, auth_token=None, email=None)
    return {"status": "account deleted"}


# ─── Chat photos ─────────────────────────────────────────────────────────────


@mcp.tool()
def save_chat_photo(media_hash: str) -> dict:
    """Add an already-uploaded image hash to your saved chat photos list."""
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/v3/me/prefs/chat-pix/{media_hash}",
            headers=_headers(),
            content=b"",
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def remove_chat_photo(media_hash: str) -> dict:
    """Remove an image hash from your saved chat photos list."""
    with httpx.Client() as client:
        resp = client.delete(
            f"{BASE_URL}/v3/me/prefs/chat-pix/{media_hash}",
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json() or {"status": "ok"}


@mcp.tool()
def profile_image_url(media_hash: str, thumbnail: bool = False) -> dict:
    """Return the CDN URL for a profile image or thumbnail given its media hash."""
    if thumbnail:
        url = f"{CDN_URL}/images/thumb/320x320/{media_hash}"
    else:
        url = f"{CDN_URL}/images/profile/1024x1024/{media_hash}"
    return {"url": url}


if __name__ == "__main__":
    mcp.run()
