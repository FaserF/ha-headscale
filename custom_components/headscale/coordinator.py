"""DataUpdateCoordinator for the Headscale integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from tailscale import Device as TailscaleDevice
from tailscale import Tailscale, TailscaleAuthenticationError

from .client import (
    HeadscaleAuthenticationError,
    HeadscaleClient,
    HeadscaleError,
    HeadscaleNode,
    HeadscaleUser,
)
from .const import (
    CONF_API_KEY,
    CONF_MODE,
    CONF_OAUTH_CLIENT_ID,
    CONF_OAUTH_CLIENT_SECRET,
    CONF_TAILNET,
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    LOGGER,
    MODE_HEADSCALE,
    SCAN_INTERVAL,
)

type HeadscaleConfigEntry = ConfigEntry[HeadscaleDataUpdateCoordinator]


@dataclass
class HeadscaleCoordinatorData:
    """Class to hold Headscale coordinator data."""

    nodes: dict[str, HeadscaleNode]
    users: list[HeadscaleUser]


class HeadscaleDataUpdateCoordinator(DataUpdateCoordinator[HeadscaleCoordinatorData]):
    """The Headscale & Tailscale Data Update Coordinator."""

    config_entry: HeadscaleConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: HeadscaleConfigEntry) -> None:
        """Initialize the coordinator."""
        self.mode = config_entry.data.get(CONF_MODE, MODE_HEADSCALE)
        self.headscale_client: HeadscaleClient | None = None
        self.tailscale_client: Tailscale | None = None
        self.previous_devices: set[str] = set()

        session = async_get_clientsession(hass)

        if self.mode == MODE_HEADSCALE:
            self.headscale_client = HeadscaleClient(
                base_url=config_entry.data[CONF_URL],
                api_key=config_entry.data[CONF_API_KEY],
                session=session,
                verify_ssl=config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
            )
        else:
            self.tailscale_client = Tailscale(
                session=session,
                oauth_client_id=config_entry.data[CONF_OAUTH_CLIENT_ID],
                oauth_client_secret=config_entry.data[CONF_OAUTH_CLIENT_SECRET],
                tailnet=config_entry.data[CONF_TAILNET],
            )

        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> HeadscaleCoordinatorData:
        """Fetch devices and users from Headscale or Tailscale."""
        if self.mode == MODE_HEADSCALE:
            assert self.headscale_client is not None
            try:
                nodes = await self.headscale_client.get_nodes()
                users: list[HeadscaleUser] = []
                try:
                    users = await self.headscale_client.get_users()
                except Exception as err:
                    LOGGER.debug("Could not fetch users: %s", err)
            except HeadscaleAuthenticationError as err:
                raise ConfigEntryAuthFailed from err
            except HeadscaleError as err:
                raise UpdateFailed(
                    f"Error communicating with Headscale: {err}"
                ) from err

            # Cleanup stale devices in HA device registry
            current_device_ids = set(nodes.keys())
            if self.previous_devices:
                stale_device_ids = self.previous_devices - current_device_ids
                if stale_device_ids:
                    await self._remove_stale_devices(stale_device_ids)
            self.previous_devices = current_device_ids

            return HeadscaleCoordinatorData(nodes=nodes, users=users)

        # MODE_TAILSCALE
        assert self.tailscale_client is not None
        try:
            ts_devices: dict[
                str, TailscaleDevice
            ] = await self.tailscale_client.devices()
        except TailscaleAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Tailscale: {err}") from err

        nodes = {}
        for dev_id, dev in ts_devices.items():
            nodes[dev_id] = HeadscaleNode(
                id=dev_id,
                name=dev.name,
                given_name=dev.name,
                addresses=dev.addresses,
                user=dev.user,
                online=dev.connected_to_control,
                last_seen=dev.last_seen,
                expires=dev.expires,
                key_expiry_disabled=dev.key_expiry_disabled,
                tags=dev.tags if hasattr(dev, "tags") else [],
                connected_to_control=dev.connected_to_control,
                update_available=dev.update_available,
                client_connectivity=dev.client_connectivity,
                raw_data={},
            )

        current_device_ids = set(nodes.keys())
        if self.previous_devices:
            stale_device_ids = self.previous_devices - current_device_ids
            if stale_device_ids:
                await self._remove_stale_devices(stale_device_ids)
        self.previous_devices = current_device_ids

        return HeadscaleCoordinatorData(nodes=nodes, users=[])

    async def _remove_stale_devices(self, stale_device_ids: set[str]) -> None:
        """Remove devices that no longer exist."""
        device_registry = dr.async_get(self.hass)

        for device_id in stale_device_ids:
            device = device_registry.async_get_device_by_identifier(
                (DOMAIN, device_id), self.config_entry.entry_id
            )
            if device:
                LOGGER.debug("Removing stale device: %s", device_id)
                device_registry.async_remove_device(device.id)
