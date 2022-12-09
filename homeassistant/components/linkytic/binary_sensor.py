"""Binary sensors for linkytic integration."""
from __future__ import annotations

import logging

# from homeassistant.components.binary_sensor import (
#     BinarySensorDeviceClass,
#     BinarySensorEntity,
# )
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import SETUP_SERIAL  # SERIAL_READER

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Linky (LiXee-TIC-DIN) binary sensor platform."""
    _LOGGER.info("Setting up binary sensor plateform")
    # Init sensors
    # async_add_entities(
    #     [SerialConnectivity(discovery_info[SERIAL_READER])], True)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    _LOGGER.info(
        "%s: config entry data: %s",
        config_entry.title,
        config_entry.data.get(SETUP_SERIAL),
    )
    _LOGGER.warning(
        "%s: config entry data: %s", config_entry.title, config_entry.options.items()
    )
