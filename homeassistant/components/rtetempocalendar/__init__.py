"""The RTE Tempo Calendar integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .api_worker import APIWorker
from .const import CONFIG_CLIEND_SECRET, CONFIG_CLIENT_ID, DOMAIN

PLATFORMS: list[Platform] = [Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up rtetempocalendar from a config entry."""
    # Create the serial reader thread and start it
    api_worker = APIWorker(
        client_id=str(entry.data.get(CONFIG_CLIENT_ID)),
        client_secret=str(entry.data.get(CONFIG_CLIEND_SECRET)),
    )
    api_worker.start()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, api_worker.signalstop)
    # Add options callback
    entry.async_on_unload(lambda: api_worker.signalstop("config_entry_unload"))
    # Add the serial reader to HA and initialize sensors
    try:
        hass.data[DOMAIN][entry.entry_id] = api_worker
    except KeyError:
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][entry.entry_id] = api_worker
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    # main init done
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove the related entry
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
