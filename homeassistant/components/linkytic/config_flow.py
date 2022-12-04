"""Config flow for linkytic integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


TIC_MODES = [
    selector.SelectOptionDict(value="hist", label="Historique"),
    selector.SelectOptionDict(value="std", label="Standard"),
]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("serial_device", default="/dev/ttyUSB0"): str,
        vol.Required("tic_mode", default="hist"): selector.SelectSelector(
            selector.SelectSelectorConfig(options=TIC_MODES),
        ),
        vol.Required("three_phase", default=False): bool,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, device: str) -> None:
        """Initialize."""
        self.device = device

    async def connect(self) -> bool:
        """Test if we can authenticate with the device."""
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    if data["tic_mode"] == "std":
        raise StandardUnsupported

    hub = PlaceholderHub(data["serial_device"])

    if not await hub.connect():
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": "Linky TIC on {}".format(data["serial_device"])}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for linkytic."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except StandardUnsupported:
            errors["base"] = "unsupported_standard"
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class StandardUnsupported(HomeAssistantError):
    """Error to indicate that the user choose the unsupported standard TIC mode."""
