"""Sensors for Custom Integrations Statistics integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import EntryAPIAccess
from .const import DOMAIN

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
        api_proxy = hass.data[DOMAIN][config_entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "%s: can not calendar: failed to get the API worker object",
            config_entry.title,
        )
        return
    # Init sensors
    sensors = [IntegrationStats(config_entry.title, config_entry.entry_id, api_proxy)]
    # Add the entities to HA
    async_add_entities(sensors, False)


class IntegrationStats(SensorEntity):
    """Integration Statistics Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:finance"

    def __init__(
        self, inte_name: str, config_id: str, api_proxy: EntryAPIAccess
    ) -> None:
        """Initialize the Current Color Sensor."""
        # Generic properties
        self._attr_name = f"{inte_name} installations"
        self._attr_unique_id = f"{DOMAIN}_{config_id}_stats"
        # Sensor entity properties
        self._attr_native_value: int | None = None
        self._attr_extra_state_attributes: dict[str, str] = {}
        # Custom entity properties
        self._inte_name = inte_name
        self._api_proxy = api_proxy
        self._api_proxy.register_entity_callback(
            self._attr_unique_id, self.data_update_callback
        )

    def data_update_callback(self):
        """Schedule an update of the sensor and a read of its value (push)."""
        self.schedule_update_ha_state(force_refresh=True)

    @callback
    def update(self):
        """Update the value of the sensor from the thread object memory cache."""
        # Get stats from cache
        try:
            stats = self._api_proxy.get_statistics(self._inte_name)
        except KeyError:
            stats = None
        if stats is None:
            self._attr_available = False
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return
        # Got them
        try:
            total = stats["total"]
            versions = stats["versions"]
        except KeyError:
            _LOGGER.error(
                "Stats for %s retrieved but failed to access known keys",
                self._inte_name,
            )
            self._attr_available = False
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return
        # Handle total
        if not isinstance(total, int):
            _LOGGER.error("Stats total for %s should be int", self._inte_name)
            self._attr_available = False
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return
        self._attr_native_value = total
        # Handle versions
        self._attr_extra_state_attributes = {}
        for version, nb_install in versions.items():
            if not isinstance(nb_install, int):
                _LOGGER.error(
                    "Version %s installs for %s should be int", version, self._inte_name
                )
                continue
            self._attr_extra_state_attributes[version] = str(nb_install)
