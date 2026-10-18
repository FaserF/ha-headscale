"""Support for Headscale and Tailscale sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import HeadscaleNode
from .coordinator import HeadscaleConfigEntry, HeadscaleDataUpdateCoordinator
from .entity import HeadscaleEntity, HeadscaleServerEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class HeadscaleSensorEntityDescription(SensorEntityDescription):
    """Describes a Headscale node sensor entity."""

    value_fn: Callable[[HeadscaleNode], datetime | str | int | None]
    attrs_fn: Callable[[HeadscaleNode], dict[str, Any]] | None = None


NODE_SENSORS: tuple[HeadscaleSensorEntityDescription, ...] = (
    HeadscaleSensorEntityDescription(
        key="expires",
        translation_key="expires",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.expires,
    ),
    HeadscaleSensorEntityDescription(
        key="ip",
        translation_key="ip",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.addresses[0] if device.addresses else None,
        attrs_fn=lambda device: {
            "addresses": device.addresses,
            "machine_key": device.machine_key,
            "node_key": device.node_key,
            "user": device.user,
            "tags": device.tags,
            "approved_routes": device.approved_routes,
            "available_routes": device.available_routes,
        },
    ),
    HeadscaleSensorEntityDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda device: device.last_seen,
    ),
    HeadscaleSensorEntityDescription(
        key="user",
        translation_key="node_user",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.user,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HeadscaleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Headscale sensors based on a config entry."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        HeadscaleSensorEntity(
            coordinator=coordinator,
            device_id=device_id,
            description=description,
        )
        for device_id in coordinator.data.nodes
        for description in NODE_SENSORS
    ]

    # Add Server Level Metrics & Stats
    entities.extend(
        [
            HeadscaleServerCountSensor(
                coordinator=coordinator,
                key="total_nodes",
                translation_key="total_nodes",
                value_fn=lambda c: len(c.data.nodes),
            ),
            HeadscaleServerCountSensor(
                coordinator=coordinator,
                key="online_nodes",
                translation_key="online_nodes",
                value_fn=lambda c: sum(
                    1
                    for n in c.data.nodes.values()
                    if n.online or n.connected_to_control
                ),
            ),
            HeadscaleServerCountSensor(
                coordinator=coordinator,
                key="total_users",
                translation_key="total_users",
                value_fn=lambda c: len(c.data.users),
            ),
        ]
    )

    async_add_entities(entities)


class HeadscaleSensorEntity(HeadscaleEntity, SensorEntity):
    """Defines a Headscale sensor for a node."""

    entity_description: HeadscaleSensorEntityDescription

    def __init__(
        self,
        coordinator: HeadscaleDataUpdateCoordinator,
        device_id: str,
        description: HeadscaleSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{device_id}_{description.key}"
        )

    @property
    @override
    def native_value(self) -> datetime | str | int | None:
        """Return the state of the sensor."""
        dev = self.device
        if dev is None:
            return None
        return self.entity_description.value_fn(dev)

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        dev = self.device
        if dev is None or not self.entity_description.attrs_fn:
            return None
        return self.entity_description.attrs_fn(dev)


class HeadscaleServerCountSensor(HeadscaleServerEntity, SensorEntity):
    """Sensor for server-wide statistics."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: HeadscaleDataUpdateCoordinator,
        key: str,
        translation_key: str,
        value_fn: Callable[[HeadscaleDataUpdateCoordinator], int],
    ) -> None:
        """Initialize count sensor."""
        super().__init__(coordinator, key)
        self._value_fn = value_fn
        self._attr_translation_key = translation_key

    @property
    @override
    def native_value(self) -> int:
        """Return count value."""
        return self._value_fn(self.coordinator)
