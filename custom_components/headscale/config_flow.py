"""Config flow for Headscale & Tailscale integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from tailscale import Tailscale, TailscaleAuthenticationError, TailscaleError

from .client import (
    HeadscaleAuthenticationError,
    HeadscaleClient,
    HeadscaleConnectionError,
    HeadscaleError,
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
    MODE_TAILSCALE,
)


class HeadscaleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Headscale and Tailscale."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step (choose provider mode)."""
        if user_input is not None:
            if user_input[CONF_MODE] == MODE_HEADSCALE:
                return await self.async_step_headscale()
            return await self.async_step_tailscale()

        return self.async_show_menu(
            step_id="user",
            menu_options=["headscale", "tailscale"],
        )

    async def async_step_headscale(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle Headscale configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input[CONF_URL].strip().rstrip("/")
            api_key = user_input[CONF_API_KEY].strip()
            verify_ssl = user_input.get(CONF_VERIFY_SSL, True)

            # Unique ID by Headscale URL
            await self.async_set_unique_id(base_url)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = HeadscaleClient(
                base_url=base_url,
                api_key=api_key,
                session=session,
                verify_ssl=verify_ssl,
            )

            try:
                await client.get_nodes()
            except HeadscaleAuthenticationError:
                errors["base"] = "invalid_auth"
            except HeadscaleConnectionError:
                errors["base"] = "cannot_connect"
            except HeadscaleError:
                errors["base"] = "unknown"
            except Exception:
                LOGGER.exception("Unexpected error connecting to Headscale")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Headscale ({base_url})",
                    data={
                        CONF_MODE: MODE_HEADSCALE,
                        CONF_URL: base_url,
                        CONF_API_KEY: api_key,
                        CONF_VERIFY_SSL: verify_ssl,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default="https://"): str,
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_VERIFY_SSL, default=True): bool,
            }
        )

        return self.async_show_form(
            step_id="headscale",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_tailscale(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle official Tailscale configuration (100% Core parity)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            tailnet = user_input[CONF_TAILNET].strip()
            client_id = user_input[CONF_OAUTH_CLIENT_ID].strip()
            client_secret = user_input[CONF_OAUTH_CLIENT_SECRET].strip()

            await self.async_set_unique_id(tailnet)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            tailscale = Tailscale(
                session=session,
                oauth_client_id=client_id,
                oauth_client_secret=client_secret,
                tailnet=tailnet,
            )

            try:
                await tailscale.devices()
            except TailscaleAuthenticationError:
                errors["base"] = "invalid_auth"
            except TailscaleError:
                errors["base"] = "cannot_connect"
            except Exception:
                LOGGER.exception("Unexpected error connecting to Tailscale")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=tailnet,
                    data={
                        CONF_MODE: MODE_TAILSCALE,
                        CONF_TAILNET: tailnet,
                        CONF_OAUTH_CLIENT_ID: client_id,
                        CONF_OAUTH_CLIENT_SECRET: client_secret,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_TAILNET): str,
                vol.Required(CONF_OAUTH_CLIENT_ID): str,
                vol.Required(CONF_OAUTH_CLIENT_SECRET): str,
            }
        )

        return self.async_show_form(
            step_id="tailscale",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow for this handler."""
        return HeadscaleOptionsFlow(config_entry)


class HeadscaleOptionsFlow(OptionsFlow):
    """Handle options for Headscale."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        if self._config_entry.data.get(CONF_MODE) == MODE_HEADSCALE:
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_VERIFY_SSL,
                            default=self._config_entry.data.get(
                                CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL
                            ),
                        ): bool,
                    }
                ),
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
