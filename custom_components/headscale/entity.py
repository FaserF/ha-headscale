"""Base entity for the Headscale and Tailscale integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import HeadscaleNode
from .const import DOMAIN
from .coordinator import HeadscaleDataUpdateCoordinator


class HeadscaleEntity(CoordinatorEntity[HeadscaleDataUpdateCoordinator]):
    """Defines a base Headscale/Tailscale device entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HeadscaleDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{device_id}"

    @property
    def device(self) -> HeadscaleNode | None:
        """Return the current device from coordinator data."""
        return self.coordinator.data.nodes.get(self.device_id)

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device info for this Tailnet node."""
        dev = self.device
        if dev is None:
            return None

        model_name = (
            "Tailscale Node"
            if self.coordinator.mode == "tailscale"
            else "Headscale Node"
        )
        return DeviceInfo(
            configuration_url=f"https://login.tailscale.com/admin/machines/{dev.addresses[0]}"
            if self.coordinator.mode == "tailscale" and dev.addresses
            else self.coordinator.config_entry.data.get("url"),
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self.device_id)},
            manufacturer="Tailscale"
            if self.coordinator.mode == "tailscale"
            else "Headscale",
            model=model_name,
            name=dev.name,
            sw_version=dev.register_method,
        )


class HeadscaleServerEntity(CoordinatorEntity[HeadscaleDataUpdateCoordinator]):
    """Defines a base entity for the Headscale server itself."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HeadscaleDataUpdateCoordinator,
        key: str,
    ) -> None:
        """Initialize the server entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_server_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for the Headscale/Tailscale control plane."""
        is_ts = self.coordinator.mode == "tailscale"
        title = "Tailscale Control Plane" if is_ts else "Headscale Control Plane"
        return DeviceInfo(
            configuration_url=self.coordinator.config_entry.data.get("url"),
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{self.coordinator.config_entry.entry_id}_server")},
            manufacturer="Tailscale" if is_ts else "Headscale",
            model="Control Plane Server",
            name=title,
        )
