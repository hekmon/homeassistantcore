"""RTE Tempo Calendar."""
from __future__ import annotations

import datetime
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api_worker import APIWorker
from .const import DOMAIN

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
        [TempoCalendar(api_worker)],
        True,
    )


class TempoCalendar(CalendarEntity):
    """Create a Home Assistant calendar returning tempo days."""

    def __init__(self, api_worker: APIWorker) -> None:
        """Initialize the calendar."""
        self._api_worker = api_worker
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
                events.append(
                    CalendarEvent(
                        start=tempo_day.Start,
                        end=tempo_day.End,
                        summary=f"tempo {tempo_day.Value} day",
                        description=f"Mis à jour à {tempo_day.Updated}",
                        uid=f"{DOMAIN}_{tempo_day.Start.year}_{tempo_day.Start.month}_{tempo_day.Start.day}",
                    )
                )
        _LOGGER.debug(
            "Returning %d events (on %d available) for range %s <> %s",
            len(events),
            len(self._api_worker.tempo_days),
            start_date,
            end_date,
        )
        return events
