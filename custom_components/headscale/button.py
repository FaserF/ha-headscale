"""Support for Headscale button actions."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HeadscaleConfigEntry, HeadscaleDataUpdateCoordinator
from .entity import HeadscaleEntity, HeadscaleServerEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HeadscaleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Headscale button entities based on a config entry."""
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = []

    # Node buttons (expire key)
    if coordinator.mode == "headscale":
        for device_id in coordinator.data.nodes:
            entities.append(
                HeadscaleExpireNodeButton(
                    coordinator=coordinator,
                    device_id=device_id,
                )
            )

    # Server button: Refresh data
    entities.append(HeadscaleRefreshButton(coordinator=coordinator))

    async_add_entities(entities)


class HeadscaleExpireNodeButton(HeadscaleEntity, ButtonEntity):
    """Button to manually expire a node's key."""

    _attr_translation_key = "expire_node"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HeadscaleDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize button."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{device_id}_expire_button"
        )

    async def async_press(self) -> None:
        """Trigger node expiration."""
        if not self.coordinator.headscale_client:
            raise HomeAssistantError("Headscale client not available.")
        try:
            await self.coordinator.headscale_client.expire_node(self.device_id)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            raise HomeAssistantError(f"Failed to expire node: {err}") from err


class HeadscaleRefreshButton(HeadscaleServerEntity, ButtonEntity):
    """Button to trigger data coordinator refresh."""

    _attr_translation_key = "refresh_data"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: HeadscaleDataUpdateCoordinator) -> None:
        """Initialize button."""
        super().__init__(coordinator, "refresh")

    async def async_press(self) -> None:
        """Trigger data refresh."""
        await self.coordinator.async_request_refresh()
