# pylint: disable=broad-exception-caught
"""The independent API controller for the Custom Integrations Statistics integration."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.aiohttp_client

from .const import REFRESH_INTERVAL, STATS_PAGE

_LOGGER = logging.getLogger(__name__)


class Singleton:
    """Inherit this class to transform child instantiation as singleton."""

    __instance: Singleton | None = None

    def __new__(cls, *args, **kwargs):
        """Return existing singleton if it exists."""
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def unload_singleton(self):
        """Nullify the current singleton."""
        __instance = None


# def register_api_client(
#     hass: HomeAssistant,
#     client_id: str,
#     callback: Callable[[], None],
# ):
#     """Register a config entry API proxy/access to the API controller singleton. Spawn the singleton is necessary."""
#     global _SINGLETON, _SINGLETON_TASK
#     # Singleton is instantiated
#     if _SINGLETON is not None:
#         total_clients = _SINGLETON.register(client_id, callback)
#         _LOGGER.debug("API controller has currently %d active client(s)", total_clients)
#         return
#     # Singleton is not instantiated, let's spawn it
#     _LOGGER.debug("API controller singleton is not instantiated, spawning it")
#     _SINGLETON = StatsAPI(hass)
#     _SINGLETON.register(client_id, callback)
#     _SINGLETON_TASK = hass.async_create_task(
#         _SINGLETON.loop(), "custstats-api-controller-singleton"
#     )


# def unregister_api_client(client_id: str):
#     """Unregister a config entry API proxy from the singleton. Stop the singleton if it was the last client."""
#     global _SINGLETON, _SINGLETON_TASK
#     # Should not happen
#     if _SINGLETON is None:
#         _LOGGER.warning(
#             "'%s' tried to unregister as an API client but the API controller singleton is not instantiated",
#             client_id,
#         )
#         return
#     # Unregister client
#     if _SINGLETON.unregister(client_id) == 0:
#         _LOGGER.debug(
#             "'%s' was the last active API client, unregistering the API controller singleton",
#             client_id,
#         )
#         if _SINGLETON_TASK is not None:
#             if not _SINGLETON_TASK.cancel():
#                 _LOGGER.warning("Cancelling api controller singleton task failed")
#             _SINGLETON_TASK = None
#         else:
#             # Should not happen
#             _LOGGER.warning("Can not stop api controller task as it is None")
#         _SINGLETON = None


# def get_integration_stats(integration: str) -> dict[str, Any] | None:
#     """Get statistics from the singleton is spawned."""
#     # global _SINGLETON
#     if _SINGLETON is None:
#         return None
#     return _SINGLETON.stats[integration]


class StatsAPI(Singleton):
    """Home Assistant Custom Integrations statistics API Controller."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the API controller."""
        _LOGGER.debug("initializing API controller singleton")
        # Controllers
        self.websession: aiohttp.ClientSession = (
            homeassistant.helpers.aiohttp_client.async_get_clientsession(hass)
        )
        # State
        self.clients: dict[str, Callable[[], None]] = {}
        self.stats: dict[str, dict[str, Any]] = {}
        self.task = hass.async_create_task(
            self.loop(), "custstats-api-controller-singleton"
        )

    async def _update_stats(self):
        async with self.websession.get(STATS_PAGE) as resp:
            # Handle response
            if resp.status == 200:
                # Parse payload
                self.stats = await resp.json()
            else:
                _LOGGER.error(
                    "Statistics fetching failed with HTTP return code %d", resp.status
                )
                self.stats = {}
        # Notify registered clients
        for client_id, client_callback in self.clients.items():
            _LOGGER.debug("notifying API client '%s' of fresh data", client_id)
            client_callback()

    async def loop(self):
        """Task periodically probbing the API and update local cached data."""
        try:
            while len(self.clients) > 0:
                _LOGGER.info("Refreshing statistics data")
                await self._update_stats()
                await asyncio.sleep(REFRESH_INTERVAL.seconds)
        except asyncio.CancelledError:
            _LOGGER.info("Stats API singleton controller task cancelled")
        except Exception as exp:
            _LOGGER.exception(
                "Unexpected exception caught during probbing loop: %s", exp
            )

    def register_api_client(self, entity_id: str, callback: Callable[[], None]) -> int:
        """Register a config entry API proxy as client."""
        _LOGGER.info("Registering '%s' as active API client", entity_id)
        self.clients[entity_id] = callback
        return len(self.clients)

    def unregister_api_client(self, entity_id: str) -> int:
        """Unregister a config entry API proxy as client."""
        _LOGGER.info("Unregistering '%s' as active API client", entity_id)
        del (self.clients, entity_id)
        if len(self.clients) == 0:
            if not self.task.cancel():
                _LOGGER.warning("Cancelling api controller singleton task failed")
            self.unload_singleton()
        return len(self.clients)


class EntryAPIAccess:
    """Allowed for a config entry to access the api controller singleton."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the proxy and register it as client against the api controller singleton."""
        # Initialize ourself
        self.id = entry.entry_id
        self.entities: dict[str, Callable[[], None]] = {}
        # Register ourself to the singleton
        self.api_singleton = StatsAPI(hass)
        self.api_singleton.register_api_client(self.id, self.api_update_callback)

    def api_update_callback(self):
        """Inform proxy when new data has been fetched. Should be used as a callback by the singleton."""
        for entity_id, entity_callback in self.entities.items():
            _LOGGER.debug("notifying entity '%s' of fresh data", entity_id)
            entity_callback()

    def get_statistics(self, integration: str) -> dict[str, Any] | None:
        """Get by proxy statistics data from singleton."""
        return self.api_singleton.stats[integration]

    def register_entity_callback(self, entity_id: str, callback: Callable[[], None]):
        """Register an entity callback to be called when singleton will inform us of new data."""
        self.entities[entity_id] = callback

    def unload(self, event):
        """Unregister ourself from the singleton controller."""
        _LOGGER.debug(
            "unloading Entry API Access for entities: received %s event", event
        )
        self.api_singleton.unregister_api_client(self.id)
