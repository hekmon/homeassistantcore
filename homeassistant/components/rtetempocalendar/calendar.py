"""RTE Tempo Calendar."""
from __future__ import annotations

import datetime
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api_worker import APIWorker, TempoDay
from .const import (
    API_ATTRIBUTION,
    API_VALUE_BLUE,
    API_VALUE_RED,
    API_VALUE_WHITE,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
    FRANCE_TZ,
)

_LOGGER = logging.getLogger(__name__)


# config flow setup
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    _LOGGER.debug("%s: setting up calendar plateform", config_entry.title)
    # Retrieve the serial reader object
    try:
        api_worker = hass.data[DOMAIN][config_entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "%s: can not calendar: failed to get the API worker object",
            config_entry.title,
        )
        return
    # Init sensors
    async_add_entities(
        [TempoCalendar(api_worker, config_entry.entry_id)],
        True,
    )


class TempoCalendar(CalendarEntity):
    """Create a Home Assistant calendar returning tempo days."""

    # Generic entity properties
    _attr_has_entity_name = True
    _attr_attribution = API_ATTRIBUTION

    def __init__(self, api_worker: APIWorker, config_id) -> None:
        """Initialize the calendar."""
        # Generic entity properties
        self._attr_name = "Calendrier"
        self._attr_unique_id = f"{DOMAIN}_{config_id}_calendar"
        # TempoCalendar properties
        self._api_worker = api_worker
        self._config_id = config_id
        super().__init__()

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        events: list[CalendarEvent] = []
        for tempo_day in self._api_worker.tempo_days:
            if tempo_day.Start >= start_date and tempo_day.End <= end_date:
                events.append(forge_calendar_event(tempo_day))
            elif tempo_day.Start < start_date < tempo_day.End < end_date:
                events.append(forge_calendar_event(tempo_day))
            elif start_date < tempo_day.Start < end_date < tempo_day.End:
                events.append(forge_calendar_event(tempo_day))
        _LOGGER.debug(
            "Returning %d events (on %d available) for range %s <> %s",
            len(events),
            len(self._api_worker.tempo_days),
            start_date,
            end_date,
        )
        return events

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

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current active event if any."""
        localized_now = datetime.datetime.now(FRANCE_TZ)
        for tempo_day in self._api_worker.tempo_days:
            if tempo_day.Start <= localized_now < tempo_day.End:
                return forge_calendar_event(tempo_day)
        return None


def forge_calendar_event(tempo_day: TempoDay):
    """Forge a Home Assistant Calendar Event from a Tempo day."""
    return CalendarEvent(
        start=tempo_day.Start,
        end=tempo_day.End,
        summary=forge_summary(tempo_day.Value),
        description=f"Mis à jour le {tempo_day.Updated}",
        uid=f"{DOMAIN}_{tempo_day.Start.year}_{tempo_day.Start.month}_{tempo_day.Start.day}",
    )


def forge_summary(value: str) -> str:
    """Forge a calendar event summary from a tempo day value."""
    if value == API_VALUE_RED:
        return "Jour Tempo Ro" + "uge 🔴"  # codespell workaround
    if value == API_VALUE_WHITE:
        return "Jour Tempo Blanc ⚪"
    if value == API_VALUE_BLUE:
        return "Jour Tempo Bleu 🔵"
    return f"Jour Tempo inconnu ({value})"
