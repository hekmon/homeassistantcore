"""Binary sensors for linkytic integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, SERIAL_READER
from .reader import LinkyTICReader

_LOGGER = logging.getLogger(__name__)


# legacy setup via YAML
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None,
) -> None:
    """Set up the Linky TIC binary sensor platform."""
    _LOGGER.debug("setting up binary sensor plateform (legacy)")
    # Init sensors
    if discovery_info:
        async_add_entities(
            [SerialConnectivity("legacy", "legacy", discovery_info[SERIAL_READER])],
            True,
        )


# config flow setup
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    _LOGGER.debug("%s: setting up binary sensor plateform", config_entry.title)
    # Retrieve the serial reader object
    try:
        serial_reader = hass.data[DOMAIN][config_entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "%s: can not init binaries sensors: failed to get the serial reader object",
            config_entry.title,
        )
        return
    # Init sensors
    async_add_devices(
        [SerialConnectivity(config_entry.title, config_entry.entry_id, serial_reader)],
        True,
    )


class SerialConnectivity(BinarySensorEntity):
    """Serial connectivity to the Linky TIC serial interface."""

    # Generic properties
    #   https://developers.home-assistant.io/docs/core/entity#generic-properties
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Linky - Connectivité du lien série"
    _attr_should_poll = True

    # Binary sensor properties
    #   https://developers.home-assistant.io/docs/core/entity/binary-sensor/#properties
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, title: str, uniqid: str, serial_reader: LinkyTICReader) -> None:
        """Initialize the SerialConnectivity binary sensor."""
        _LOGGER.debug("%s initializing SerialConnectivity binary sensor", title)
        self._title = title
        self._attr_unique_id = "linky_serial_connectivity__" + uniqid
        self._serial_controller = serial_reader

    @property
    def is_on(self) -> bool:
        """Value of the sensor."""
        return self._serial_controller.is_connected()
