"""The linkytic integration serial reader."""
from __future__ import annotations

import logging
import threading
import time

_LOGGER = logging.getLogger(__name__)


class LinkyTICReader(threading.Thread):
    """Implements the reading of a serial Linky TIC."""

    def __init__(self, title: str, real_time: bool | None) -> None:
        """Init the LinkyTIC thread serial reader."""
        if real_time is None:
            real_time = False
        self._realtime = real_time
        self._stopsignal = False
        self._title = title
        super().__init__(name=title)

    def run(self):
        """Continuously read the the serial connection and extract TIC values."""
        while not self._stopsignal:
            _LOGGER.info("Ticking (real time: %s)", self._realtime)
            time.sleep(3)
        _LOGGER.warning("Serial reading stopped")

    def stop(self, event):
        """Activate the stop flag in order to stop the thread from within."""
        _LOGGER.warning("Stopping %s (received %s)", self._title, event)
        self._stopsignal = True

    def update_options(self, real_time: bool):
        """Setter to update serial reader options."""
        _LOGGER.warning("%s: new real time option value: %s", self._title, real_time)
        self._realtime = real_time
