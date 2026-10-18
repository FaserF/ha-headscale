"""Client abstractions for Headscale REST API and Tailscale compatibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiohttp


class HeadscaleError(Exception):
    """Base exception for Headscale client."""


class HeadscaleAuthenticationError(HeadscaleError):
    """Authentication failure in Headscale API."""


class HeadscaleConnectionError(HeadscaleError):
    """Connection failure in Headscale API."""


@dataclass
class HeadscaleUser:
    """Represents a Headscale user."""

    id: str
    name: str
    created_at: str | None = None
    display_name: str | None = None
    email: str | None = None


@dataclass
class HeadscalePreAuthKey:
    """Represents a Headscale PreAuthKey."""

    id: str
    key: str
    user: str
    reusable: bool
    ephemeral: bool
    used: bool
    expiration: str | None = None
    created_at: str | None = None


@dataclass
class HeadscaleNode:
    """Represents a unified node (Headscale or Tailscale)."""

    id: str
    name: str
    given_name: str
    addresses: list[str] = field(default_factory=list)
    user: str | None = None
    online: bool = False
    last_seen: datetime | None = None
    expires: datetime | None = None
    key_expiry_disabled: bool = False
    tags: list[str] = field(default_factory=list)
    approved_routes: list[str] = field(default_factory=list)
    available_routes: list[str] = field(default_factory=list)
    subnet_routes: list[str] = field(default_factory=list)
    machine_key: str | None = None
    node_key: str | None = None
    disco_key: str | None = None
    register_method: str | None = None
    # Compatibility attributes with Tailscale Core Device model
    connected_to_control: bool = False
    update_available: bool = False
    client_connectivity: Any = None
    raw_data: dict[str, Any] = field(default_factory=dict)


def parse_datetime(val: str | None) -> datetime | None:
    """Parse ISO datetime string safely."""
    if not val:
        return None
    try:
        if val.endswith("Z"):
            val = val[:-1] + "+00:00"
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class HeadscaleClient:
    """REST Client for Headscale v1 API."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        session: aiohttp.ClientSession,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize Headscale REST client."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = session
        self.verify_ssl = verify_ssl

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        """Perform HTTP request against Headscale API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._headers()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        ssl = kwargs.pop("ssl", None)
        if ssl is None and not self.verify_ssl:
            ssl = False

        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                ssl=ssl,
                **kwargs,
            ) as response:
                if response.status in (401, 403):
                    text = await response.text()
                    raise HeadscaleAuthenticationError(
                        f"Authentication failed: {response.status} - {text}"
                    )
                if response.status >= 400:
                    text = await response.text()
                    raise HeadscaleError(
                        f"Headscale API error {response.status}: {text}"
                    )

                if response.status == 204:
                    return None

                return await response.json()
        except aiohttp.ClientError as err:
            raise HeadscaleConnectionError(
                f"Error connecting to Headscale server: {err}"
            ) from err

    async def get_nodes(self) -> dict[str, HeadscaleNode]:
        """Fetch all nodes from Headscale server."""
        data = await self.request("GET", "/api/v1/node")
        nodes_raw = data.get("nodes", [])
        result: dict[str, HeadscaleNode] = {}

        for item in nodes_raw:
            node_id = str(item.get("id"))
            user_info = item.get("user")
            username = user_info.get("name") if isinstance(user_info, dict) else None

            last_seen = parse_datetime(item.get("lastSeen"))
            expires = parse_datetime(item.get("expiry"))
            key_expiry_disabled = expires is None

            online = bool(item.get("online", False))

            node = HeadscaleNode(
                id=node_id,
                name=item.get("name", f"node-{node_id}"),
                given_name=item.get("givenName") or item.get("name", f"node-{node_id}"),
                addresses=item.get("ipAddresses", []),
                user=username,
                online=online,
                last_seen=last_seen,
                expires=expires,
                key_expiry_disabled=key_expiry_disabled,
                tags=item.get("tags", []),
                approved_routes=item.get("approvedRoutes", []),
                available_routes=item.get("availableRoutes", []),
                subnet_routes=item.get("subnetRoutes", []),
                machine_key=item.get("machineKey"),
                node_key=item.get("nodeKey"),
                disco_key=item.get("discoKey"),
                register_method=item.get("registerMethod"),
                connected_to_control=online,
                update_available=False,
                client_connectivity=None,
                raw_data=item,
            )
            result[node_id] = node

        return result

    async def get_users(self) -> list[HeadscaleUser]:
        """Fetch all users from Headscale server."""
        data = await self.request("GET", "/api/v1/user")
        users_raw = data.get("users", [])
        return [
            HeadscaleUser(
                id=str(u.get("id")),
                name=u.get("name", ""),
                created_at=u.get("createdAt"),
                display_name=u.get("displayName"),
                email=u.get("email"),
            )
            for u in users_raw
        ]

    async def create_user(self, name: str) -> dict[str, Any]:
        """Create a new user in Headscale."""
        return await self.request("POST", "/api/v1/user", json={"name": name})

    async def rename_user(self, old_id: str, new_name: str) -> dict[str, Any]:
        """Rename an existing user."""
        return await self.request("POST", f"/api/v1/user/{old_id}/rename/{new_name}")

    async def delete_node(self, node_id: str) -> None:
        """Delete a node from Headscale."""
        await self.request("DELETE", f"/api/v1/node/{node_id}")

    async def expire_node(self, node_id: str) -> dict[str, Any]:
        """Expire a node registration in Headscale."""
        return await self.request("POST", f"/api/v1/node/{node_id}/expire")

    async def rename_node(self, node_id: str, new_name: str) -> dict[str, Any]:
        """Rename a node in Headscale."""
        return await self.request("POST", f"/api/v1/node/{node_id}/rename/{new_name}")

    async def set_node_tags(self, node_id: str, tags: list[str]) -> dict[str, Any]:
        """Set tags for a node."""
        return await self.request(
            "POST", f"/api/v1/node/{node_id}/tags", json={"tags": tags}
        )

    async def set_approved_routes(
        self, node_id: str, routes: list[str]
    ) -> dict[str, Any]:
        """Approve subnet routes for a node."""
        return await self.request(
            "POST",
            f"/api/v1/node/{node_id}/approve_routes",
            json={"routes": routes},
        )

    async def get_preauthkeys(self, user: str) -> list[HeadscalePreAuthKey]:
        """Get pre-auth keys for a user."""
        data = await self.request("GET", f"/api/v1/preauthkey?user={user}")
        keys_raw = data.get("preAuthKeys", [])
        return [
            HeadscalePreAuthKey(
                id=str(k.get("id")),
                key=k.get("key", ""),
                user=user,
                reusable=bool(k.get("reusable", False)),
                ephemeral=bool(k.get("ephemeral", False)),
                used=bool(k.get("used", False)),
                expiration=k.get("expiration"),
                created_at=k.get("createdAt"),
            )
            for k in keys_raw
        ]

    async def create_preauthkey(
        self,
        user: str,
        reusable: bool = False,
        ephemeral: bool = False,
        expiration: str | None = None,
        acl_tags: list[str] | None = None,
    ) -> HeadscalePreAuthKey:
        """Create a pre-auth key for a user."""
        payload: dict[str, Any] = {
            "user": user,
            "reusable": reusable,
            "ephemeral": ephemeral,
        }
        if expiration:
            payload["expiration"] = expiration
        if acl_tags:
            payload["aclTags"] = acl_tags

        data = await self.request("POST", "/api/v1/preauthkey", json=payload)
        key_data = data.get("preAuthKey", {})
        return HeadscalePreAuthKey(
            id=str(key_data.get("id")),
            key=key_data.get("key", ""),
            user=user,
            reusable=bool(key_data.get("reusable", False)),
            ephemeral=bool(key_data.get("ephemeral", False)),
            used=bool(key_data.get("used", False)),
            expiration=key_data.get("expiration"),
            created_at=key_data.get("createdAt"),
        )

    async def expire_preauthkey(self, user: str, key: str) -> None:
        """Expire a pre-auth key."""
        await self.request(
            "POST",
            "/api/v1/preauthkey/expire",
            json={"user": user, "key": key},
        )
