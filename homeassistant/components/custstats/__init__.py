"""The Custom Integrations Statistics integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .api import EntryAPIAccess
from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up custstats from a config entry."""
    # Create the serial reader thread and start it
    api_proxy = EntryAPIAccess(hass, entry)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, api_proxy.unload)
    entry.async_on_unload(lambda: api_proxy.unload("config_entry_unload"))
    # Add the APIProxy to HA and initialize sensors
    try:
        hass.data[DOMAIN][entry.entry_id] = api_proxy
    except KeyError:
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][entry.entry_id] = api_proxy
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # main init done
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
