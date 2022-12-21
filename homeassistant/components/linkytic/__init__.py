"""The linkytic integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType

from .const import (  # config flow; legacy
    CONF_SERIAL_PORT,
    CONF_STANDARD_MODE,
    CONF_THREE_PHASE,
    DEFAULT_SERIAL_PORT,
    DEFAULT_STANDARD_MODE,
    DEFAULT_THREE_PHASE,
    DOMAIN,
    OPTIONS_REALTIME,
    SERIAL_READER,
    SETUP_SERIAL,
    TICMODE_HISTORIC,
)
from .serial_reader import LinkyTICReader

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


# legacy yaml based setup
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SERIAL_PORT, default=DEFAULT_SERIAL_PORT): cv.string,
                vol.Required(
                    CONF_STANDARD_MODE, default=DEFAULT_STANDARD_MODE
                ): cv.boolean,
                vol.Required(CONF_THREE_PHASE, default=DEFAULT_THREE_PHASE): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Linky TIC component."""
    _LOGGER.debug("YAML config: init linkytic component with %s", config)
    # Debug conf
    conf: Any = config.get(DOMAIN)
    if not conf:
        _LOGGER.debug(
            "YAML config: called without conf, must be config flow config, exiting"
        )
        return True
    _LOGGER.debug("YAML config: serial port: %s", conf[CONF_SERIAL_PORT])
    _LOGGER.debug("YAML config: standard mode: %s", conf[CONF_STANDARD_MODE])
    # create the serial controller and start it in a thread
    _LOGGER.info("Starting the serial reader thread")
    serial_reader = LinkyTICReader(
        title="YAML Config (legacy)",
        port=conf[CONF_SERIAL_PORT],
        std_mode=conf[CONF_STANDARD_MODE],
    )
    serial_reader.start()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, serial_reader.signalstop)
    # setup the plateforms
    hass.async_create_task(
        async_load_platform(
            hass, BINARY_SENSOR_DOMAIN, DOMAIN, {SERIAL_READER: serial_reader}, config
        )
    )
    hass.async_create_task(
        async_load_platform(
            hass,
            SENSOR_DOMAIN,
            DOMAIN,
            {
                SERIAL_READER: serial_reader,
                CONF_THREE_PHASE: conf[CONF_THREE_PHASE],
                CONF_STANDARD_MODE: conf[CONF_STANDARD_MODE],
            },
            config,
        )
    )
    return True


# config flow setup
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up linkytic from a config entry."""
    # Create the serial reader thread and start it
    serial_reader = LinkyTICReader(
        title=entry.title,
        port=entry.data.get(SETUP_SERIAL),
        std_mode=entry.data.get(TICMODE_HISTORIC),
        real_time=entry.options.get(OPTIONS_REALTIME),
    )
    serial_reader.start()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, serial_reader.signalstop)
    # Add options callback
    entry.async_on_unload(entry.add_update_listener(update_listener))
    entry.async_on_unload(lambda: serial_reader.signalstop("config_entry_unload"))
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


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    _LOGGER.warning("Update listener")
    # Retrieved the serial reader for this config entry
    try:
        serial_reader = hass.data[DOMAIN][entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "Can not update options for %s: failed to get the serial reader object",
            entry.title,
        )
        return
    # Update its options
    serial_reader.update_options(entry.options.get(OPTIONS_REALTIME))
