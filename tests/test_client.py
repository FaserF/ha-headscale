"""Tests for Headscale client and data models."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.headscale.client import (
    HeadscaleAuthenticationError,
    HeadscaleClient,
    parse_datetime,
)


@pytest.fixture
def mock_session():
    """Mock aiohttp ClientSession."""
    return MagicMock()


async def test_parse_datetime():
    """Test date parsing utility."""
    assert parse_datetime(None) is None
    assert parse_datetime("invalid") is None
    dt = parse_datetime("2026-10-18T05:00:00Z")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 18


async def test_get_nodes_success(mock_session):
    """Test getting nodes from Headscale."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "nodes": [
                {
                    "id": "1",
                    "name": "oracle-vm",
                    "givenName": "oracle-vm",
                    "ipAddresses": ["100.64.0.1", "fd7a:115c:a1e0::1"],
                    "user": {"id": "1", "name": "fabian"},
                    "online": True,
                    "lastSeen": "2026-10-18T01:57:24Z",
                    "expiry": None,
                    "tags": ["tag:server"],
                    "approvedRoutes": ["0.0.0.0/0", "::/0"],
                    "availableRoutes": ["0.0.0.0/0", "::/0"],
                    "subnetRoutes": ["0.0.0.0/0", "::/0"],
                },
                {
                    "id": "2",
                    "name": "homeassistant",
                    "givenName": "homeassistant",
                    "ipAddresses": ["100.64.0.2"],
                    "user": {"id": "1", "name": "fabian"},
                    "online": True,
                    "lastSeen": "2026-10-18T03:33:58Z",
                    "expiry": None,
                    "tags": [],
                    "approvedRoutes": ["192.168.1.0/24"],
                    "availableRoutes": ["192.168.1.0/24"],
                    "subnetRoutes": ["192.168.1.0/24"],
                },
                {
                    "id": "3",
                    "name": "dell-worker",
                    "givenName": "dell-worker",
                    "ipAddresses": ["100.64.0.3"],
                    "user": {"id": "1", "name": "fabian"},
                    "online": False,
                    "lastSeen": "2026-10-18T03:06:39Z",
                    "expiry": None,
                    "tags": [],
                    "approvedRoutes": [],
                    "availableRoutes": [],
                    "subnetRoutes": [],
                },
            ]
        }
    )

    mock_session.request = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    client = HeadscaleClient("https://vpn.fabiseitz.de:8443", "test-key", mock_session)
    nodes = await client.get_nodes()

    assert len(nodes) == 3
    assert "1" in nodes
    assert "2" in nodes
    assert "3" in nodes

    node1 = nodes["1"]
    assert node1.name == "oracle-vm"
    assert node1.online is True
    assert node1.addresses == ["100.64.0.1", "fd7a:115c:a1e0::1"]
    assert "0.0.0.0/0" in node1.approved_routes
    assert node1.key_expiry_disabled is True

    node2 = nodes["2"]
    assert node2.name == "homeassistant"
    assert "192.168.1.0/24" in node2.approved_routes

    node3 = nodes["3"]
    assert node3.online is False


async def test_get_users(mock_session):
    """Test getting users."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "users": [
                {
                    "id": "1",
                    "name": "fabian",
                    "createdAt": "2026-10-16T00:49:14Z",
                }
            ]
        }
    )
    mock_session.request = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    client = HeadscaleClient("https://vpn.fabiseitz.de:8443", "test-key", mock_session)
    users = await client.get_users()

    assert len(users) == 1
    assert users[0].id == "1"
    assert users[0].name == "fabian"


async def test_auth_error(mock_session):
    """Test 401 Unauthorized raises HeadscaleAuthenticationError."""
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.text = AsyncMock(return_value="Unauthorized")

    mock_session.request = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    client = HeadscaleClient("https://vpn.example.com:8443", "bad-key", mock_session)
    with pytest.raises(HeadscaleAuthenticationError):
        await client.get_nodes()


async def test_client_actions(mock_session):
    """Test node actions (rename, delete, tags, approve routes)."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"status": "ok"})

    mock_session.request = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    client = HeadscaleClient("https://vpn.fabiseitz.de:8443", "test-key", mock_session)

    # Expire node
    await client.expire_node("1")
    # Rename node
    await client.rename_node("1", "oracle-renamed")
    # Set tags
    await client.set_node_tags("1", ["tag:srv"])
    # Set approved routes
    await client.set_approved_routes("1", ["10.0.0.0/8"])
    # Delete node
    mock_response.status = 204
    await client.delete_node("1")
