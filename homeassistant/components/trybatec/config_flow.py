"""Config flow for Trybatec integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import APIError, TrybatecAPI
from .const import CONFIG_PASSWORD, CONFIG_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONFIG_USERNAME): str,
        vol.Required(CONFIG_PASSWORD): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Trybatec integration."""

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
        await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONFIG_USERNAME]}")
        self._abort_if_unique_id_configured()
        errors = {}
        try:
            api = TrybatecAPI(
                session=async_get_clientsession(HomeAssistant()),
                username=user_input[CONFIG_USERNAME],
                password=user_input[CONFIG_PASSWORD],
            )
            await api.test_login()
        except APIError as api_error:
            _LOGGER.error("Application validation failed: network error: %s", api_error)
            errors["base"] = "api_error"
        else:
            return self.async_create_entry(
                title=user_input[CONFIG_USERNAME], data=user_input
            )
        # Show errors
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
