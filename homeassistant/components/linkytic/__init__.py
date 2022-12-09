"""The linkytic integration."""
from __future__ import annotations

import logging
import threading
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]

_LOGGER = logging.getLogger(__name__)


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


class LinkyTICReader(threading.Thread):
    """Implements the reading of a serial Linky TIC."""

    def __init__(self, name):
        """Init the LinkyTIC thread serial reader."""
        self._stopsignal = False
        super().__init__(name=name)

    def run(self):
        """Continuously read the the serial connection and extract TIC values."""
        while not self._stopsignal:
            _LOGGER.info("Ticking")
            time.sleep(3)
        _LOGGER.warning("Serial reading stopped")

    def stop(self, event):
        """Activate the stop flag in order to stop the thread from within."""
        _LOGGER.warning("Stopping %s (received %s)", self._name, event)
        self._stopsignal = True
