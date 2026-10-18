"""Support for Headscale route switches."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HeadscaleConfigEntry, HeadscaleDataUpdateCoordinator
from .entity import HeadscaleEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HeadscaleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Headscale switch entities based on a config entry."""
    coordinator = entry.runtime_data
    if coordinator.mode != "headscale":
        return

    entities: list[SwitchEntity] = []

    # For each node with available subnet routes, create a switch per route
    for device_id, node in coordinator.data.nodes.items():
        for route in node.available_routes:
            entities.append(
                HeadscaleRouteSwitch(
                    coordinator=coordinator,
                    device_id=device_id,
                    route=route,
                )
            )

    async_add_entities(entities)


class HeadscaleRouteSwitch(HeadscaleEntity, SwitchEntity):
    """Switch to approve or revoke a subnet route for a node."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HeadscaleDataUpdateCoordinator,
        device_id: str,
        route: str,
    ) -> None:
        """Initialize route switch."""
        super().__init__(coordinator, device_id)
        self.route = route
        safe_route = route.replace("/", "_").replace(":", "_").replace(".", "_")
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{device_id}_route_{safe_route}"
        )
        self._attr_name = f"Route {route}"

    @property
    def is_on(self) -> bool:
        """Return True if route is approved."""
        dev = self.device
        if dev is None:
            return False
        return self.route in dev.approved_routes

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Approve this route."""
        dev = self.device
        if dev is None or not self.coordinator.headscale_client:
            raise HomeAssistantError("Node or client not available.")

        new_routes = sorted(set(dev.approved_routes + [self.route]))
        try:
            await self.coordinator.headscale_client.set_approved_routes(
                self.device_id, new_routes
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            raise HomeAssistantError(
                f"Failed to approve route {self.route}: {err}"
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Revoke this route approval."""
        dev = self.device
        if dev is None or not self.coordinator.headscale_client:
            raise HomeAssistantError("Node or client not available.")

        new_routes = [r for r in dev.approved_routes if r != self.route]
        try:
            await self.coordinator.headscale_client.set_approved_routes(
                self.device_id, new_routes
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            raise HomeAssistantError(
                f"Failed to revoke route {self.route}: {err}"
            ) from err
