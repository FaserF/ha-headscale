"""Support for Headscale and Tailscale binary sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import HeadscaleNode
from .coordinator import HeadscaleConfigEntry, HeadscaleDataUpdateCoordinator
from .entity import HeadscaleEntity, HeadscaleServerEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class HeadscaleBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Headscale binary sensor entity."""

    is_on_fn: Callable[[HeadscaleNode], bool | None]


BINARY_SENSORS: tuple[HeadscaleBinarySensorEntityDescription, ...] = (
    HeadscaleBinarySensorEntityDescription(
        key="connected_to_control",
        translation_key="connected_to_control",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda device: device.online or device.connected_to_control,
    ),
    HeadscaleBinarySensorEntityDescription(
        key="update_available",
        translation_key="client",
        device_class=BinarySensorDeviceClass.UPDATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda device: device.update_available,
    ),
    HeadscaleBinarySensorEntityDescription(
        key="key_expiry_disabled",
        translation_key="key_expiry_disabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda device: device.key_expiry_disabled,
    ),
    HeadscaleBinarySensorEntityDescription(
        key="client_supports_ipv6",
        translation_key="client_supports_ipv6",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda device: (
            device.client_connectivity.client_supports.ipv6
            if device.client_connectivity is not None
            and hasattr(device.client_connectivity, "client_supports")
            else None
        ),
    ),
    HeadscaleBinarySensorEntityDescription(
        key="client_supports_pcp",
        translation_key="client_supports_pcp",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda device: (
            device.client_connectivity.client_supports.pcp
            if device.client_connectivity is not None
            and hasattr(device.client_connectivity, "client_supports")
            else None
        ),
    ),
    HeadscaleBinarySensorEntityDescription(
        key="client_supports_pmp",
        translation_key="client_supports_pmp",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda device: (
            device.client_connectivity.client_supports.pmp
            if device.client_connectivity is not None
            and hasattr(device.client_connectivity, "client_supports")
            else None
        ),
    ),
    HeadscaleBinarySensorEntityDescription(
        key="client_supports_udp",
        translation_key="client_supports_udp",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda device: (
            device.client_connectivity.client_supports.udp
            if device.client_connectivity is not None
            and hasattr(device.client_connectivity, "client_supports")
            else None
        ),
    ),
    HeadscaleBinarySensorEntityDescription(
        key="client_supports_upnp",
        translation_key="client_supports_upnp",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda device: (
            device.client_connectivity.client_supports.upnp
            if device.client_connectivity is not None
            and hasattr(device.client_connectivity, "client_supports")
            else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HeadscaleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Headscale binary sensors based on a config entry."""
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        HeadscaleBinarySensorEntity(
            coordinator=coordinator,
            device_id=device_id,
            description=description,
        )
        for device_id in coordinator.data.nodes
        for description in BINARY_SENSORS
    ]

    # Server-level binary sensor for overall control plane health
    entities.append(HeadscaleServerOnlineBinarySensor(coordinator=coordinator))

    async_add_entities(entities)


class HeadscaleBinarySensorEntity(HeadscaleEntity, BinarySensorEntity):
    """Defines a Headscale binary sensor for a node."""

    entity_description: HeadscaleBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: HeadscaleDataUpdateCoordinator,
        device_id: str,
        description: HeadscaleBinarySensorEntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{device_id}_{description.key}"
        )

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the state of the sensor."""
        dev = self.device
        if dev is None:
            return None
        return self.entity_description.is_on_fn(dev)


class HeadscaleServerOnlineBinarySensor(HeadscaleServerEntity, BinarySensorEntity):
    """Defines a server online binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "server_online"

    def __init__(self, coordinator: HeadscaleDataUpdateCoordinator) -> None:
        """Initialize server online sensor."""
        super().__init__(coordinator, "online")

    @property
    @override
    def is_on(self) -> bool:
        """Return True if last update was successful."""
        return self.coordinator.last_update_success
