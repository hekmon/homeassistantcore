"""The linkytic integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .reader import LinkyTICReader

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up linkytic from a config entry."""
    # Create the serial reader thread and start it
    serial_reader = LinkyTICReader(entry.title)
    serial_reader.start()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, serial_reader.stop)
    # Add the serial reader to HA and initialize sensors
    try:
        hass.data[DOMAIN][entry.entry_id] = serial_reader
    except KeyError:
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][entry.entry_id] = serial_reader
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove the related entry
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
