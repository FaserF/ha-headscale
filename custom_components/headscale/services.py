"""Services for the Headscale integration."""

from __future__ import annotations

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError

from .const import (
    ATTR_EXPIRATION,
    ATTR_KEY,
    ATTR_NEW_NAME,
    ATTR_NEW_USER,
    ATTR_NODE_ID,
    ATTR_OLD_USER,
    ATTR_REUSABLE,
    ATTR_ROUTES,
    ATTR_TAGS,
    ATTR_USER,
    DOMAIN,
    SERVICE_CREATE_PREAUTHKEY,
    SERVICE_CREATE_USER,
    SERVICE_DELETE_NODE,
    SERVICE_EXPIRE_NODE,
    SERVICE_EXPIRE_PREAUTHKEY,
    SERVICE_RENAME_NODE,
    SERVICE_RENAME_USER,
    SERVICE_SET_APPROVED_ROUTES,
    SERVICE_SET_NODE_TAGS,
)
from .coordinator import HeadscaleDataUpdateCoordinator

SCHEMA_EXPIRE_NODE = vol.Schema(
    {
        vol.Required(ATTR_NODE_ID): cv.string,
    }
)

SCHEMA_RENAME_NODE = vol.Schema(
    {
        vol.Required(ATTR_NODE_ID): cv.string,
        vol.Required(ATTR_NEW_NAME): cv.string,
    }
)

SCHEMA_DELETE_NODE = vol.Schema(
    {
        vol.Required(ATTR_NODE_ID): cv.string,
    }
)

SCHEMA_SET_NODE_TAGS = vol.Schema(
    {
        vol.Required(ATTR_NODE_ID): cv.string,
        vol.Required(ATTR_TAGS): vol.All(cv.ensure_list, [cv.string]),
    }
)

SCHEMA_SET_APPROVED_ROUTES = vol.Schema(
    {
        vol.Required(ATTR_NODE_ID): cv.string,
        vol.Required(ATTR_ROUTES): vol.All(cv.ensure_list, [cv.string]),
    }
)

SCHEMA_CREATE_PREAUTHKEY = vol.Schema(
    {
        vol.Required(ATTR_USER): cv.string,
        vol.Optional(ATTR_REUSABLE, default=False): cv.boolean,
        vol.Optional("ephemeral", default=False): cv.boolean,
        vol.Optional(ATTR_EXPIRATION): cv.string,
        vol.Optional(ATTR_TAGS): vol.All(cv.ensure_list, [cv.string]),
    }
)

SCHEMA_EXPIRE_PREAUTHKEY = vol.Schema(
    {
        vol.Required(ATTR_USER): cv.string,
        vol.Required(ATTR_KEY): cv.string,
    }
)

SCHEMA_CREATE_USER = vol.Schema(
    {
        vol.Required(ATTR_USER): cv.string,
    }
)

SCHEMA_RENAME_USER = vol.Schema(
    {
        vol.Required(ATTR_OLD_USER): cv.string,
        vol.Required(ATTR_NEW_USER): cv.string,
    }
)


def _get_coordinator(hass: HomeAssistant) -> HeadscaleDataUpdateCoordinator:
    """Return the first active Headscale coordinator."""
    entries = hass.config_entries.async_entries(DOMAIN)
    for entry in entries:
        if hasattr(entry, "runtime_data") and entry.runtime_data:
            return entry.runtime_data
    raise HomeAssistantError("No active Headscale integration entry found.")


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration services."""

    async def handle_expire_node(call: ServiceCall) -> None:
        coord = _get_coordinator(hass)
        if not coord.headscale_client:
            raise HomeAssistantError("Expire node is only supported in Headscale mode.")
        node_id = call.data[ATTR_NODE_ID]
        await coord.headscale_client.expire_node(node_id)
        await coord.async_request_refresh()

    async def handle_rename_node(call: ServiceCall) -> None:
        coord = _get_coordinator(hass)
        if not coord.headscale_client:
            raise HomeAssistantError("Rename node is only supported in Headscale mode.")
        node_id = call.data[ATTR_NODE_ID]
        new_name = call.data[ATTR_NEW_NAME]
        await coord.headscale_client.rename_node(node_id, new_name)
        await coord.async_request_refresh()

    async def handle_delete_node(call: ServiceCall) -> None:
        coord = _get_coordinator(hass)
        if not coord.headscale_client:
            raise HomeAssistantError("Delete node is only supported in Headscale mode.")
        node_id = call.data[ATTR_NODE_ID]
        await coord.headscale_client.delete_node(node_id)
        await coord.async_request_refresh()

    async def handle_set_node_tags(call: ServiceCall) -> None:
        coord = _get_coordinator(hass)
        if not coord.headscale_client:
            raise HomeAssistantError(
                "Tag management is only supported in Headscale mode."
            )
        node_id = call.data[ATTR_NODE_ID]
        tags = call.data[ATTR_TAGS]
        await coord.headscale_client.set_node_tags(node_id, tags)
        await coord.async_request_refresh()

    async def handle_set_approved_routes(call: ServiceCall) -> None:
        coord = _get_coordinator(hass)
        if not coord.headscale_client:
            raise HomeAssistantError(
                "Route approval is only supported in Headscale mode."
            )
        node_id = call.data[ATTR_NODE_ID]
        routes = call.data[ATTR_ROUTES]
        await coord.headscale_client.set_approved_routes(node_id, routes)
        await coord.async_request_refresh()

    async def handle_create_preauthkey(call: ServiceCall) -> dict[str, str]:
        coord = _get_coordinator(hass)
        if not coord.headscale_client:
            raise HomeAssistantError(
                "Pre-auth keys are only supported in Headscale mode."
            )
        user = call.data[ATTR_USER]
        reusable = call.data[ATTR_REUSABLE]
        ephemeral = call.data["ephemeral"]
        expiration = call.data.get(ATTR_EXPIRATION)
        tags = call.data.get(ATTR_TAGS)
        key = await coord.headscale_client.create_preauthkey(
            user=user,
            reusable=reusable,
            ephemeral=ephemeral,
            expiration=expiration,
            acl_tags=tags,
        )
        return {"key": key.key, "id": key.id, "expiration": key.expiration or ""}

    async def handle_expire_preauthkey(call: ServiceCall) -> None:
        coord = _get_coordinator(hass)
        if not coord.headscale_client:
            raise HomeAssistantError(
                "Pre-auth keys are only supported in Headscale mode."
            )
        user = call.data[ATTR_USER]
        key = call.data[ATTR_KEY]
        await coord.headscale_client.expire_preauthkey(user=user, key=key)

    async def handle_create_user(call: ServiceCall) -> None:
        coord = _get_coordinator(hass)
        if not coord.headscale_client:
            raise HomeAssistantError(
                "User creation is only supported in Headscale mode."
            )
        user = call.data[ATTR_USER]
        await coord.headscale_client.create_user(user)
        await coord.async_request_refresh()

    async def handle_rename_user(call: ServiceCall) -> None:
        coord = _get_coordinator(hass)
        if not coord.headscale_client:
            raise HomeAssistantError("User rename is only supported in Headscale mode.")
        old_user = call.data[ATTR_OLD_USER]
        new_user = call.data[ATTR_NEW_USER]
        await coord.headscale_client.rename_user(old_user, new_user)
        await coord.async_request_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_EXPIRE_NODE, handle_expire_node, schema=SCHEMA_EXPIRE_NODE
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RENAME_NODE, handle_rename_node, schema=SCHEMA_RENAME_NODE
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_NODE, handle_delete_node, schema=SCHEMA_DELETE_NODE
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_NODE_TAGS, handle_set_node_tags, schema=SCHEMA_SET_NODE_TAGS
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_APPROVED_ROUTES,
        handle_set_approved_routes,
        schema=SCHEMA_SET_APPROVED_ROUTES,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_PREAUTHKEY,
        handle_create_preauthkey,
        schema=SCHEMA_CREATE_PREAUTHKEY,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPIRE_PREAUTHKEY,
        handle_expire_preauthkey,
        schema=SCHEMA_EXPIRE_PREAUTHKEY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CREATE_USER, handle_create_user, schema=SCHEMA_CREATE_USER
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RENAME_USER, handle_rename_user, schema=SCHEMA_RENAME_USER
    )
