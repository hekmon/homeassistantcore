"""Config flow for linkytic integration."""
from __future__ import annotations

# import dataclasses
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries

# from homeassistant.components.usb import UsbServiceInfo
from homeassistant.core import HomeAssistant, callback
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
        vol.Required("serial_device", default="/dev/ttyUSB1"): str,
        vol.Required("tic_mode", default="hist"): selector.SelectSelector(
            selector.SelectSelectorConfig(options=TIC_MODES),
        ),
        vol.Required("three_phase", default=False): bool,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for linkytic."""

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
        # Input provided
        await self.async_set_unique_id(DOMAIN + "_" + user_input["serial_device"])
        self._abort_if_unique_id_configured()
        # Try to connect
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

    # async def async_step_usb(self, discovery_info: UsbServiceInfo) -> FlowResult:
    #     """Handle a flow initialized by USB discovery."""
    #     return await self.async_step_discovery(dataclasses.asdict(discovery_info))

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class StandardUnsupported(HomeAssistantError):
    """Error to indicate that the user choose the unsupported standard TIC mode."""


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
                        "real_time", default=self.config_entry.options.get("real_time")
                    ): bool
                }
            ),
        )


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
