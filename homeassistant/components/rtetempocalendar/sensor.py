"""Sensors for RTE Tempo Calendar integration."""
from __future__ import annotations

import asyncio
import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api_worker import APIWorker
from .const import (
    API_ATTRIBUTION,
    API_REQ_TIMEOUT,
    API_VALUE_BLUE,
    API_VALUE_RED,
    API_VALUE_WHITE,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
    FRANCE_TZ,
    SENSOR_COLOR_BLUE_EMOJI,
    SENSOR_COLOR_BLUE_NAME,
    SENSOR_COLOR_RED_EMOJI,
    SENSOR_COLOR_RED_NAME,
    SENSOR_COLOR_UNKNOWN_EMOJI,
    SENSOR_COLOR_UNKNOWN_NAME,
    SENSOR_COLOR_WHITE_EMOJI,
    SENSOR_COLOR_WHITE_NAME,
)

_LOGGER = logging.getLogger(__name__)


# config flow setup
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Modern (thru config entry) sensors setup."""
    _LOGGER.debug("%s: setting up sensor plateform", config_entry.title)
    # Retrieve the API Worker object
    try:
        api_worker = hass.data[DOMAIN][config_entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "%s: can not calendar: failed to get the API worker object",
            config_entry.title,
        )
        return
    # Wait request timeout to let API worker get first batch of data before initializing calendar
    await asyncio.sleep(API_REQ_TIMEOUT)
    # Init sensors
    sensors = [
        CurrentColor(config_entry.entry_id, api_worker, False),
        CurrentColor(config_entry.entry_id, api_worker, True),
        NextColor(config_entry.entry_id, api_worker, False),
        NextColor(config_entry.entry_id, api_worker, True),
    ]
    # Add the entities to HA
    async_add_entities(sensors, True)


class CurrentColor(SensorEntity):
    """Current Color Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_attribution = API_ATTRIBUTION
    # Sensor properties
    # _attr_device_class = SensorDeviceClass.ENUM  # will have to wait until next release
    _attr_icon = "mdi:palette"

    def __init__(self, config_id: str, api_worker: APIWorker, emoji: bool) -> None:
        """Initialize the Current Color Sensor."""
        # Generic entity properties
        if emoji:
            self._attr_name = "Couleur actuelle (emoji)"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_current_color_emoji"
            # self._attr_options = [
            #     SENSOR_COLOR_BLUE_EMOJI,
            #     SENSOR_COLOR_WHITE_EMOJI,
            #     SENSOR_COLOR_RED_EMOJI,
            #     SENSOR_COLOR_UNKNOWN_EMOJI,
            # ]  # will have to wait until next release
        else:
            self._attr_name = "Couleur actuelle"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_current_color"
            # self._attr_options = [
            #     SENSOR_COLOR_BLUE_NAME,
            #     SENSOR_COLOR_WHITE_NAME,
            #     SENSOR_COLOR_RED_NAME,
            #     SENSOR_COLOR_UNKNOWN_NAME,
            # ]  # will have to wait until next release
        # Sensor entity properties
        self._attr_native_value: str | None = None
        # RTE Tempo Calendar entity properties
        self._config_id = config_id
        self._api_worker = api_worker
        self._emoji = emoji

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    @callback
    def update(self):
        """Update the value of the sensor from the thread object memory cache."""
        localized_now = datetime.datetime.now(FRANCE_TZ)
        for tempo_day in self._api_worker.get_adjusted_days():
            if tempo_day.Start <= localized_now < tempo_day.End:
                # Found a match !
                self._attr_available = True
                if self._emoji:
                    self._attr_native_value = get_color_emoji(tempo_day.Value)
                else:
                    self._attr_native_value = get_color_name(tempo_day.Value)
                return
        # Nothing found
        self._attr_available = False
        self._attr_native_value = None


class NextColor(SensorEntity):
    """Next Color Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_attribution = API_ATTRIBUTION
    # Sensor properties
    # _attr_device_class = SensorDeviceClass.ENUM  # will have to wait until next release
    _attr_icon = "mdi:palette"

    def __init__(self, config_id: str, api_worker: APIWorker, emoji: bool) -> None:
        """Initialize the Next Color Sensor."""
        # Generic entity properties
        if emoji:
            self._attr_name = "Prochaine couleur (emoji)"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_next_color_emoji"
            # self._attr_options = [
            #     SENSOR_COLOR_BLUE_EMOJI,
            #     SENSOR_COLOR_WHITE_EMOJI,
            #     SENSOR_COLOR_RED_EMOJI,
            #     SENSOR_COLOR_UNKNOWN_EMOJI,
            # ]  # will have to wait until next release
        else:
            self._attr_name = "Prochaine couleur"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_next_color"
            # self._attr_options = [
            #     SENSOR_COLOR_BLUE_NAME,
            #     SENSOR_COLOR_WHITE_NAME,
            #     SENSOR_COLOR_RED_NAME,
            #     SENSOR_COLOR_UNKNOWN_NAME,
            # ]  # will have to wait until next release
        # Sensor entity properties
        self._attr_native_value: str | None = None
        # RTE Tempo Calendar entity properties
        self._config_id = config_id
        self._api_worker = api_worker
        self._emoji = emoji

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    @callback
    def update(self):
        """Update the value of the sensor from the thread object memory cache."""
        localized_now = datetime.datetime.now(FRANCE_TZ)
        for tempo_day in self._api_worker.get_adjusted_days():
            if localized_now < tempo_day.Start:
                # Found a match !
                self._attr_available = True
                if self._emoji:
                    self._attr_native_value = get_color_emoji(tempo_day.Value)
                else:
                    self._attr_native_value = get_color_name(tempo_day.Value)
                return
        # Special case for emoji
        if self._emoji:
            self._attr_available = True
            self._attr_native_value = SENSOR_COLOR_UNKNOWN_EMOJI
        else:
            self._attr_available = False
            self._attr_native_value = None


def get_color_emoji(value: str) -> str:
    """Return the corresponding emoji for a day color."""
    if value == API_VALUE_RED:
        return SENSOR_COLOR_RED_EMOJI
    if value == API_VALUE_WHITE:
        return SENSOR_COLOR_WHITE_EMOJI
    if value == API_VALUE_BLUE:
        return SENSOR_COLOR_BLUE_EMOJI
    _LOGGER.warning("Can not get color emoji for unknown value: %s", value)
    return SENSOR_COLOR_UNKNOWN_EMOJI


def get_color_name(value: str) -> str:
    """Return the corresponding emoji for a day color."""
    if value == API_VALUE_RED:
        return SENSOR_COLOR_RED_NAME
    if value == API_VALUE_WHITE:
        return SENSOR_COLOR_WHITE_NAME
    if value == API_VALUE_BLUE:
        return SENSOR_COLOR_BLUE_NAME
    _LOGGER.warning("Can not get color name for unknown value: %s", value)
    return SENSOR_COLOR_UNKNOWN_NAME
