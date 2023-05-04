# pylint: disable=broad-exception-caught
"""Sensors for RTE Tempo Calendar integration."""
from __future__ import annotations

import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import (
    APIError,
    TrybatecAPI,
    cleanup_str,
    generate_entity_picture,
    parse_iso_date,
)
from .const import (  # DEVICE_PAYLOAD_STATE,
    DEVICE_PAYLOAD_ACTIVATION_DATE,
    DEVICE_PAYLOAD_EMIT_SN,
    DEVICE_PAYLOAD_ID,
    DEVICE_PAYLOAD_LOCALISATION,
    DEVICE_PAYLOAD_NAME,
    DEVICE_PAYLOAD_NAME_CODE,
    DEVICE_PAYLOAD_NAME_CODE_COLDWATER,
    DEVICE_PAYLOAD_NAME_CODE_HEAT,
    DEVICE_PAYLOAD_NAME_CODE_HOTWATER,
    DEVICE_PAYLOAD_NAME_ID,
    DEVICE_PAYLOAD_PICTURE,
    DEVICE_PAYLOAD_RESIDENCE,
    DEVICE_PAYLOAD_SHARE,
    DEVICE_PAYLOAD_SN,
    DEVICE_PAYLOAD_TYPE,
    DOMAIN,
    FRANCE_TZ,
    OPTION_REAL_IMAGES,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(hours=1)


class InvalidType(Exception):
    """Invalid type error."""

    def __init__(self, *args: object) -> None:
        """Initialize invalid type error."""
        super().__init__(*args)


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
        api: TrybatecAPI = hass.data[DOMAIN][config_entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "%s: can not calendar: failed to get the API worker object",
            config_entry.title,
        )
        return
    # Fetch available devices
    try:
        devices = await api.get_devices()
        _LOGGER.info("%s: recovered %d devices", config_entry.title, len(devices))
    except APIError as exc:
        _LOGGER.exception(
            "%s: can not init sensors: failed to get devices: %s",
            config_entry.title,
            exc,
        )
        return
    # Build sensors
    sensors = []
    for device in devices:
        try:
            sensors.append(
                Consumption(device_info=device, config_entry=config_entry, api=api)
            )
        except KeyError as exc:
            _LOGGER.exception(
                "%s: failed to add device as sensor (KeyError '%s'): %s",
                config_entry.title,
                exc,
                device,
            )
        except InvalidType:
            _LOGGER.warning(
                "%s: failed to add device as sensor (unknown type '%s'): %s",
                config_entry.title,
                device[DEVICE_PAYLOAD_NAME_CODE],
                device,
            )
    # Add the sensors to HA
    async_add_entities(sensors, True)


class Consumption(SensorEntity):
    """Consumption Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    # Sensor properties
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self, device_info: dict[str, str], config_entry: ConfigEntry, api: TrybatecAPI
    ) -> None:
        """Initialize the Cold Water Sensor Entity."""
        # Generic properties
        self._attr_name = device_info[DEVICE_PAYLOAD_NAME]
        self._attr_unique_id = (
            f"{DOMAIN}_{config_entry.entry_id}_{device_info[DEVICE_PAYLOAD_NAME_CODE]}"
        )
        clean_residence = cleanup_str(device_info[DEVICE_PAYLOAD_RESIDENCE])
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{clean_residence}_{device_info[DEVICE_PAYLOAD_SHARE]}")
            },
            entry_type=DeviceEntryType.SERVICE,
            manufacturer=DOMAIN.capitalize(),
            model="Individualisation de la consommation",
            name=f"{clean_residence} Lot {device_info[DEVICE_PAYLOAD_SHARE]}",
        )
        self._attr_extra_state_attributes: dict[str, str] = {
            # "État du compteur": device_info[DEVICE_PAYLOAD_STATE],
            "Localisation": device_info[DEVICE_PAYLOAD_LOCALISATION],
            "Type de compteur": device_info[DEVICE_PAYLOAD_TYPE],
            "N° de série": device_info[DEVICE_PAYLOAD_SN],
            "N° de série émetteur": device_info[DEVICE_PAYLOAD_EMIT_SN],
            "Date de mise en service": parse_iso_date(
                device_info[DEVICE_PAYLOAD_ACTIVATION_DATE]
            ).strftime("Le %d/%m/%Y à %H:%M:%S"),
        }
        # Sensor entity properties
        self._attr_native_value: int | None = None
        # Device type related entity properties
        if device_info[DEVICE_PAYLOAD_NAME_CODE] == DEVICE_PAYLOAD_NAME_CODE_COLDWATER:
            self._attr_icon = "mdi:water"
            self._attr_device_class = SensorDeviceClass.WATER
            self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
        elif device_info[DEVICE_PAYLOAD_NAME_CODE] == DEVICE_PAYLOAD_NAME_CODE_HOTWATER:
            self._attr_icon = "mdi:water-thermometer"
            self._attr_device_class = SensorDeviceClass.WATER
            self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
        elif device_info[DEVICE_PAYLOAD_NAME_CODE] == DEVICE_PAYLOAD_NAME_CODE_HEAT:
            self._attr_icon = "mdi:radiator"
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        else:
            raise InvalidType(
                f"unexpected fluid code '{device_info[DEVICE_PAYLOAD_NAME_CODE]}'"
            )
        # Custom entity properties
        self._config_entry = config_entry
        self._api = api
        self._device_id = device_info[DEVICE_PAYLOAD_ID]
        self._fluid_id = int(device_info[DEVICE_PAYLOAD_NAME_ID])
        self._device_picture_url = generate_entity_picture(
            device_info[DEVICE_PAYLOAD_PICTURE]
        )
        self._last_valid_value_time: datetime.datetime | None = None
        self._log_prefix = f"{config_entry.title}: {clean_residence} Lot {device_info[DEVICE_PAYLOAD_SHARE]} - {device_info[DEVICE_PAYLOAD_NAME]}"

    async def async_update(self):
        """Update the value of the sensor from the API."""
        # Only update once a day
        now = datetime.datetime.now(tz=FRANCE_TZ)
        if self._last_valid_value_time is not None:
            if now.date() == self._last_valid_value_time.date():
                _LOGGER.debug(
                    "%s: we already have data for today: skipping API update",
                    self._log_prefix,
                )
                return
            _LOGGER.debug(
                "%s: data is too old (%s): proceeding with API update",
                self._log_prefix,
                self._last_valid_value_time,
            )
        # Get data from API
        try:
            data = await self._api.get_data(self._device_id, self._fluid_id)
        except APIError as exc:
            _LOGGER.exception(
                "%s: failed to recover data from API: %s", self._log_prefix, exc
            )
            return
        if len(data) == 0:
            _LOGGER.debug("%s: no data recovered", self._log_prefix)
            self._attr_native_value = None
            self._attr_available = False
            return
        _LOGGER.debug("%s: recovered data: %s", self._log_prefix, data)
        # Parse data
        self._attr_native_value = None
        self._attr_available = False
        # self._attr_available = True
        # self._last_valid_value_time = now

    @property
    def entity_picture(self) -> str | None:
        """Picture URL of the entity."""
        if self._config_entry.options.get(OPTION_REAL_IMAGES):
            return self._device_picture_url
        return None
