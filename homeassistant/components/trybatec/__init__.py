"""The Trybatec integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TrybatecAPI
from .const import CONFIG_PASSWORD, CONFIG_USERNAME, DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up rtetempo from a config entry."""
    # Create the API controller
    api = TrybatecAPI(
        session=async_get_clientsession(hass),
        username=str(entry.data.get(CONFIG_USERNAME)),
        password=str(entry.data.get(CONFIG_PASSWORD)),
    )
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, api.cleanup)
    # Save the API controller for sensors
    try:
        hass.data[DOMAIN][entry.entry_id] = api
    except KeyError:
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][entry.entry_id] = api
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # main init done
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove the related entry
        api: TrybatecAPI = hass.data[DOMAIN].pop(entry.entry_id)
        api.cleanup(Event("unload_entry"))
    return unload_ok
