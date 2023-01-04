"""Config flow for RTE Tempo Calendar."""
from __future__ import annotations

# import dataclasses
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

# from homeassistant.components.usb import UsbServiceInfo
from homeassistant.data_entry_flow import FlowResult

from .const import CONFIG_CLIEND_SECRET, CONFIG_CLIENT_ID, DOMAIN, OPTION_ADJUSTED_DAYS

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONFIG_CLIENT_ID): str,
        vol.Required(CONFIG_CLIEND_SECRET): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RTE Tempo Calendar."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # No input
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )
        # Validate input
        await self.async_set_unique_id(DOMAIN)  # only one configuration allowed
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input[CONFIG_CLIENT_ID] == "":
            errors["base"] = "no_client_id"
        elif user_input[CONFIG_CLIEND_SECRET] == "":
            errors["base"] = "no_client_secret"
        else:
            return self.async_create_entry(
                title=user_input[CONFIG_CLIENT_ID], data=user_input
            )
        # Show errors
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles the options of a Linky TIC connection."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPTION_ADJUSTED_DAYS,
                        default=self.config_entry.options.get(OPTION_ADJUSTED_DAYS),
                    ): bool
                }
            ),
        )
