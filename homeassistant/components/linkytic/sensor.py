"""Sensors for Linky TIC integration."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ELECTRIC_CURRENT_AMPERE,
    ENERGY_WATT_HOUR,
    POWER_VOLT_AMPERE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_STANDARD_MODE,
    CONF_THREE_PHASE,
    CONSTRUCTORS_CODES,
    DEVICE_TYPES,
    DID_CONSTRUCTOR,
    DID_REGNUMBER,
    DID_TYPE,
    DID_YEAR,
    DOMAIN,
    SERIAL_READER,
    SETUP_THREEPHASE,
    SETUP_TICMODE,
    TICMODE_STANDARD,
)
from .reader import LinkyTICReader

_LOGGER = logging.getLogger(__name__)


# legacy setup via YAML
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Legacy (thru YAML config) platform setup."""
    if discovery_info:
        serial_reader = discovery_info[SERIAL_READER]
    else:
        _LOGGER.error(
            "YAML config: Can not init sensor plateform with empty discovery info"
        )
        return
    await async_init(
        "YAML config",
        None,
        discovery_info[CONF_STANDARD_MODE],
        discovery_info[CONF_THREE_PHASE],
        serial_reader,
        async_add_entities,
    )


# config flow setup
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Modern (thru config entry) sensors setup."""
    _LOGGER.debug("%s: setting up binary sensor plateform", config_entry.title)
    # Retrieve the serial reader object
    try:
        serial_reader = hass.data[DOMAIN][config_entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "%s: can not init sensors: failed to get the serial reader object",
            config_entry.title,
        )
        return
    # Init sensors
    await async_init(
        config_entry.title,
        config_entry.entry_id,
        config_entry.data.get(SETUP_TICMODE) == TICMODE_STANDARD,
        bool(config_entry.data.get(SETUP_THREEPHASE)),
        serial_reader,
        async_add_devices,
    )


# factorized init
async def async_init(
    title: str,
    uniq_id: str | None,
    std_mode: bool,
    three_phase: bool,
    serial_reader: LinkyTICReader,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Linky TIC sensor platform."""
    # Wait a bit for the controller to feed on serial frames (home assistant warns after 10s)
    _LOGGER.debug(
        "%s: waiting at most 9s before setting up sensor plateform in order for the async serial reader to have time to parse a full frame",
        title,
    )
    for i in range(9):
        await asyncio.sleep(1)
        if serial_reader.has_read_full_frame():
            _LOGGER.debug("%s: a full frame has been read, initializing sensors", title)
            break
        if i == 8:
            _LOGGER.warning(
                "%s: wait time is over but a full frame has yet to be read: initializing sensors anyway",
                title,
            )
    # Init sensors
    sensors = []
    if std_mode:
        _LOGGER.error(
            "%s: standard mode is not supported (yet ?): no entities will be spawned",
            title,
        )
    else:
        # historic mode
        if three_phase:
            _LOGGER.error(
                "%s: three-phase historic mode is not supported (yet ?): no entities will be spawned",
                title,
            )
        else:
            # single phase
            sensors = [
                ADCOSensor(title, uniq_id, serial_reader),
                RegularStrSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "OPTARIF",
                    "Option tarifaire choisie",
                    "mdi:cash-check",
                    category=EntityCategory.CONFIG,
                ),
                RegularIntSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "ISOUSC",
                    "Intensité souscrite",
                    category=EntityCategory.CONFIG,
                    device_class=SensorDeviceClass.CURRENT,
                    native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
                ),
                EnergyIndexSensor(
                    title, uniq_id, serial_reader, "BASE", "Index option Base"
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "HCHC",
                    "Index option Heures Creuses - Heures Creuses",
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "HCHP",
                    "Index option Heures Creuses - Heures Pleines",
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "EJPHN",
                    "Index option EJP - Heures Normal"
                    + "es",  # workaround for codespell in HA pre commit hook
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "EJPHPM",
                    "Index option EJP - Heures de Pointe Mobile",
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "BBRHCJB",
                    "Index option Tempo - Heures Creuses Jours Bleus",
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "BBRHPJB",
                    "Index option Tempo - Heures Pleines Jours Bleus",
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "BBRHCJW",
                    "Index option Tempo - Heures Creuses Jours Blancs",
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "BBRHPJW",
                    "Index option Tempo - Heures Pleines Jours Blancs",
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "BBRHCJR",
                    "Index option Tempo - Heures Creuses Jours Rouges",
                ),
                EnergyIndexSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "BBRHPJR",
                    "Index option Tempo - Heures Pleines Jours Rouges",
                ),
                PEJPSensor(title, uniq_id, serial_reader),
                RegularStrSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "PTEC",
                    "Période Tarifaire en cours",
                    "mdi:calendar-expand-horizontal",
                ),
                RegularStrSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "DEMAIN",
                    "Couleur du lendemain",
                    "mdi:palette",
                ),
                RegularIntSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "IINST",
                    "Intensité Instantanée",
                    device_class=SensorDeviceClass.CURRENT,
                    native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                RegularIntSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "ADPS",
                    "Avertissement de Dépassement De Puissance Souscrite",
                    device_class=SensorDeviceClass.CURRENT,
                    native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                RegularIntSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "IMAX",
                    "Intensité maximale appelée",
                    device_class=SensorDeviceClass.CURRENT,
                    native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
                ),
                RegularIntSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "PAPP",
                    "Puissance apparente",
                    device_class=SensorDeviceClass.APPARENT_POWER,
                    native_unit_of_measurement=POWER_VOLT_AMPERE,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                RegularStrSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "HHPHC",
                    "Horaire Heures Pleines Heures Creuses",
                    "mdi:clock-outline",
                    enabled_by_default=False,
                ),
                RegularStrSensor(
                    title,
                    uniq_id,
                    serial_reader,
                    "MOTDETAT",
                    "Mo"
                    + "t d'état du compteur",  # workaround for codespell in HA pre commit hook
                    "mdi:file-word-box-outline",
                    category=EntityCategory.DIAGNOSTIC,
                    enabled_by_default=False,
                ),
            ]
            _LOGGER.info(
                "Adding %d sensors for the single phase historic mode", len(sensors)
            )
    if len(sensors) > 0:
        async_add_entities(sensors, False)


class ADCOSensor(SensorEntity):
    """Ad resse du compteur entity."""

    _extra: dict[str, str] = {}

    # Generic properties
    #   https://developers.home-assistant.io/docs/core/entity#generic-properties
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = (
        "Linky - A" + "dress" + "e du compteur"
    )  # workaround for codespell in HA pre commit hook
    _attr_should_poll = True
    _attr_unique_id = "linky_adco"
    _attr_icon = "mdi:tag"

    def __init__(
        self, title: str, uniq_id: str | None, serial_reader: LinkyTICReader
    ) -> None:
        """Initialize an ADCO Sensor."""
        _LOGGER.debug("%s: initializing ADCO sensor", title)
        self._title = title
        self._attr_unique_id = (
            "linky_adco" if uniq_id is None else f"{DOMAIN}_{uniq_id}_adco"
        )
        self._serial_controller = serial_reader
        self._tag = "ADCO"

    @property
    def native_value(self) -> str | None:
        """Value of the sensor."""
        value, _ = self._serial_controller.get_values(self._tag)
        _LOGGER.debug(
            "%s: recovered ADCO value from serial controller: %s", self._title, value
        )
        if value is None:
            if self._attr_available and self._serial_controller.has_read_full_frame():
                _LOGGER.info(
                    "%s: marking the ADCO sensor as unavailable: a full frame has been read but ADCO has not been found",
                    self._title,
                )
                self._attr_available = False
            return value
        # else
        # update extra info by parsing value
        self.parse_ads(value)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Get HA sensor extra attributes."""
        return self._extra

    @callback
    def update(self):
        """Update the value of the sensor from the thread object memory cache."""
        value, _ = self._serial_controller.get_values(self._tag)
        _LOGGER.debug(
            "%s: recovered %s value from serial controller: %s",
            self._title,
            self._tag,
            repr(value),
        )
        if value is None:
            if self._attr_available and self._serial_controller.has_read_full_frame():
                _LOGGER.info(
                    "%s: marking the %s sensor as unavailable: a full frame has been read but %s has not been found",
                    self._title,
                    self._tag,
                    self._tag,
                )
                self._attr_available = False
        else:
            if not self._attr_available:
                _LOGGER.info(
                    "%s: marking the %s sensor as available now ! (was not previously)",
                    self._title,
                    self._tag,
                )
                self._attr_available = True

    def parse_ads(self, ads):
        """Extract information contained in the ADS as EURIDIS."""
        if len(ads) != 12:
            _LOGGER.error(
                "%s: ADS should be 12 char long, actually %d cannot parse: %s",
                self._title,
                len(ads),
                ads,
            )
            self._extra = {}
            return
        # let's parse ADS as EURIDIS
        device_identification = {DID_YEAR: ads[2:4], DID_REGNUMBER: ads[6:]}
        # # Parse constructor code
        constructor_code = ads[0:2]
        try:
            device_identification[DID_CONSTRUCTOR] = CONSTRUCTORS_CODES[
                constructor_code
            ]
        except KeyError:
            _LOGGER.warning(
                "%s: constructor code is unknown: %s", self._title, constructor_code
            )
            device_identification[DID_CONSTRUCTOR] = None
        # # Parse device type code
        device_type = ads[4:6]
        try:
            device_identification[
                DID_TYPE
            ] = f"{DEVICE_TYPES[device_type]} ({device_type})"
        except KeyError:
            _LOGGER.warning(
                "%s: ADS device type is unknown: %s", self._title, device_type
            )
            device_identification[DID_TYPE] = None
        # Parsing done
        _LOGGER.debug("%s: parsed ADS: %s", self._title, repr(device_identification))
        # # Update main thread with device infos
        self._serial_controller.device_identification = device_identification
        # # Set this sensor extra attributes
        constructor_str = (
            f"{device_identification[DID_CONSTRUCTOR]} ({constructor_code})"
            if device_identification[DID_CONSTRUCTOR] is not None
            else f"Inconnu ({constructor_code})"
        )
        type_str = (
            f"{device_identification[DID_TYPE]} ({device_type})"
            if device_identification[DID_TYPE] is not None
            else f"Inconnu ({device_type})"
        )
        self._extra = {
            "constructeur": constructor_str,
            "année de construction": f"20{device_identification[DID_YEAR]}",
            "type de l'appareil": type_str,
            "matricule de l'appareil": device_identification[DID_REGNUMBER],
        }


class RegularStrSensor(SensorEntity):
    """Common class for text sensor."""

    # Generic entity properties
    #   https://developers.home-assistant.io/docs/core/entity#generic-properties
    _attr_should_poll = True

    def __init__(
        self,
        title: str,
        uniq_id: str | None,
        serial_reader: LinkyTICReader,
        tag: str,
        name: str,
        icon: str | None = None,
        category: EntityCategory | None = None,
        enabled_by_default: bool = True,
    ) -> None:
        """Initialize a Regular Str Sensor."""
        _LOGGER.debug("%s: initializing %s sensor", title, tag.upper())
        self._title = title
        self._serial_controller = serial_reader
        self._tag = tag.upper()
        # Generic entity properties
        if category:
            self._attr_entity_category = category
        self._attr_name = f"Linky - {name}"
        self._attr_unique_id = (
            f"linky_{tag.lower()}"
            if uniq_id is None
            else f"{DOMAIN}_{uniq_id}_{tag.lower()}"
        )
        if icon:
            self._attr_icon = icon
        self._attr_entity_registry_enabled_default = enabled_by_default

    @property
    def native_value(self) -> str | None:
        """Value of the sensor."""
        value, _ = self._serial_controller.get_values(self._tag)
        return value

    @callback
    def update(self):
        """Update the value of the sensor from the thread object memory cache."""
        value, _ = self._serial_controller.get_values(self._tag)
        _LOGGER.debug(
            "%s: recovered %s value from serial controller: %s",
            self._title,
            self._tag,
            repr(value),
        )
        if value is None:
            if self._attr_available and self._serial_controller.has_read_full_frame():
                _LOGGER.info(
                    "%s: marking the %s sensor as unavailable: a full frame has been read but %s has not been found",
                    self._title,
                    self._tag,
                    self._tag,
                )
                self._attr_available = False
        else:
            if not self._attr_available:
                _LOGGER.info(
                    "%s: marking the %s sensor as available now ! (was not previously)",
                    self._title,
                    self._tag,
                )
                self._attr_available = True


class RegularIntSensor(SensorEntity):
    """Common class for energy index counters."""

    # Generic entity properties
    #   https://developers.home-assistant.io/docs/core/entity#generic-properties
    _attr_should_poll = True

    def __init__(
        self,
        title: str,
        uniq_id: str | None,
        serial_reader: LinkyTICReader,
        tag: str,
        name: str,
        icon: str | None = None,
        category: EntityCategory | None = None,
        device_class: SensorDeviceClass | None = None,
        native_unit_of_measurement: str | None = None,
        state_class: SensorStateClass | None = None,
    ) -> None:
        """Initialize a Regular Int Sensor."""
        _LOGGER.debug("%s: initializing %s sensor", title, tag.upper())
        self._title = title
        self._serial_controller = serial_reader
        self._tag = tag.upper()
        # Generic entity properties
        if category:
            self._attr_entity_category = category
        self._attr_name = f"Linky - {name}"
        self._attr_unique_id = (
            f"linky_{tag.lower()}"
            if uniq_id is None
            else f"{DOMAIN}_{uniq_id}_{tag.lower()}"
        )
        if icon:
            self._attr_icon = icon
        # Sensor Entity Properties
        if device_class:
            self._attr_device_class = device_class
        if native_unit_of_measurement:
            self._attr_native_unit_of_measurement = native_unit_of_measurement
        if state_class:
            self._attr_state_class = state_class

    @property
    def native_value(self) -> int | None:
        """Value of the sensor."""
        raw_value, _ = self._serial_controller.get_values(self._tag)
        if raw_value is not None:
            return int(raw_value)
        # else
        return None

    @callback
    def update(self):
        """Update the value of the sensor from the thread object memory cache."""
        value, _ = self._serial_controller.get_values(self._tag)
        _LOGGER.debug(
            "%s: recovered %s value from serial controller: %s",
            self._title,
            self._tag,
            repr(value),
        )
        if value is None:
            if self._attr_available and self._serial_controller.has_read_full_frame():
                _LOGGER.info(
                    "%s: marking the %s sensor as unavailable: a full frame has been read but %s has not been found",
                    self._title,
                    self._tag,
                    self._tag,
                )
                self._attr_available = False
        else:
            if not self._attr_available:
                _LOGGER.info(
                    "%s: marking the %s sensor as available now ! (was not previously)",
                    self._title,
                    self._tag,
                )
                self._attr_available = True


class EnergyIndexSensor(RegularIntSensor):
    """Common class for energy index counters."""

    def __init__(
        self,
        title: str,
        uniq_id: str | None,
        serial_reader: LinkyTICReader,
        tag: str,
        name: str,
    ) -> None:
        """Initialize an Energy Index sensor."""
        super().__init__(
            title,
            uniq_id,
            serial_reader,
            tag,
            name,
            icon="mdi:counter",
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement=ENERGY_WATT_HOUR,
            state_class=SensorStateClass.TOTAL_INCREASING,
        )


class PEJPSensor(SensorEntity):
    """Préavis Début EJP (30 min) sensor."""

    #
    # This sensor could be improved I think (minutes as integer), but I do not have it to check and test its values
    # Leaving it as it is to facilitate future modifications
    #

    # Generic properties
    #   https://developers.home-assistant.io/docs/core/entity#generic-properties
    _attr_name = "Linky - Préavis Début EJP"
    _attr_should_poll = True
    _attr_unique_id = "linky_pejp"
    _attr_icon = "mdi:clock-start"

    def __init__(
        self, title: str, uniq_id: str | None, serial_reader: LinkyTICReader
    ) -> None:
        """Initialize a PEJP sensor."""
        _LOGGER.debug("%s: initializing PEJP sensor", title)
        self._title = title
        self._serial_controller = serial_reader
        self._tag = "PEJP"
        self._attr_unique_id = (
            "linky_pejp" if uniq_id is None else f"{DOMAIN}_{uniq_id}_pejp"
        )

    @property
    def native_value(self) -> str | None:
        """Value of the sensor."""
        value, _ = self._serial_controller.get_values(self._tag)
        return value

    @callback
    def update(self):
        """Update the value of the sensor from the thread object memory cache."""
        value, _ = self._serial_controller.get_values(self._tag)
        _LOGGER.debug(
            "%s: recovered %s value from serial controller: %s",
            self._title,
            self._tag,
            repr(value),
        )
        if value is None:
            if self._attr_available and self._serial_controller.has_read_full_frame():
                _LOGGER.info(
                    "%s: marking the %s sensor as unavailable: a full frame has been read but %s has not been found",
                    self._title,
                    self._tag,
                    self._tag,
                )
                self._attr_available = False
        else:
            if not self._attr_available:
                _LOGGER.info(
                    "%s: marking the %s sensor as available now ! (was not previously)",
                    self._title,
                    self._tag,
                )
                self._attr_available = True
