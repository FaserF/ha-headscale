"""Diagnostics support for Headscale and Tailscale."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import HeadscaleConfigEntry

TO_REDACT = {
    "api_key",
    "oauth_client_secret",
    "key",
    "machine_key",
    "node_key",
    "disco_key",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HeadscaleConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    nodes_data = {}
    for node_id, node in coordinator.data.nodes.items():
        nodes_data[node_id] = {
            "id": node.id,
            "name": node.name,
            "given_name": node.given_name,
            "addresses": node.addresses,
            "user": node.user,
            "online": node.online,
            "last_seen": node.last_seen.isoformat() if node.last_seen else None,
            "expires": node.expires.isoformat() if node.expires else None,
            "tags": node.tags,
            "approved_routes": node.approved_routes,
            "available_routes": node.available_routes,
        }

    users_data = [
        {
            "id": u.id,
            "name": u.name,
            "created_at": u.created_at,
        }
        for u in coordinator.data.users
    ]

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "mode": coordinator.mode,
        "nodes": async_redact_data(nodes_data, TO_REDACT),
        "users": users_data,
    }
