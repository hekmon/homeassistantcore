"""API worker for RTE Tempo Calendar."""
from __future__ import annotations

import datetime
import logging
import threading
from typing import NamedTuple

from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests import Response
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from homeassistant.core import callback

from .const import (
    API_DATE_FORMAT,
    API_HOUR_OF_CHANGE,
    API_KEY_END,
    API_KEY_ERROR,
    API_KEY_ERROR_DESC,
    API_KEY_RESULTS,
    API_KEY_START,
    API_KEY_UPDATED,
    API_KEY_VALUE,
    API_KEY_VALUES,
    API_REQ_TIMEOUT,
    API_TEMPO_ENDPOINT,
    API_TOKEN_ENDPOINT,
    API_VALUE_BLUE,
    FRANCE_TZ,
)

_LOGGER = logging.getLogger(__name__)


class TempoDay(NamedTuple):
    """Represents a tempo day."""

    Start: datetime.datetime | datetime.date
    End: datetime.datetime | datetime.date
    Value: str
    Updated: datetime.datetime


# https://data.rte-france.com/documents/20182/224298/FR_GU_API_Tempo_Like_Supply_Contract_v01.02.pdf


class APIWorker(threading.Thread):
    """API Worker is an autonomous thread querying, parsing an caching the RTE Tempo calendar API in an optimal way."""

    def __init__(self, client_id: str, client_secret: str, adjusted_days: bool) -> None:
        """Initialize the API Worker thread."""
        # Thread
        self._stopevent = threading.Event()
        # OAuth
        self._auth = HTTPBasicAuth(client_id, client_secret)
        self._oauth = OAuth2Session(
            client=BackendApplicationClient(client_id=client_id)
        )
        # Worker
        self._tempo_days_time: list[TempoDay] = []
        self._tempo_days_date: list[TempoDay] = []
        self.adjusted_days: bool = adjusted_days
        # Init parent thread class
        super().__init__(name="RTE Tempo Calendar API Worker")

    def get_calendar_days(self) -> list[TempoDay]:
        """Get the tempo days suited for calendar."""
        if self.adjusted_days:
            return self._tempo_days_time
        return self._tempo_days_date

    def get_adjusted_days(self) -> list[TempoDay]:
        """Get the tempo adjusted days."""
        return self._tempo_days_time

    def run(self):
        """Execute thread payload."""
        _LOGGER.info("Starting thread")
        stop = False
        while not stop:
            # First auth
            if self._oauth.token == {}:
                self._get_access_token()
            # Fetch data
            localized_now = datetime.datetime.now(FRANCE_TZ)
            end = self._update_tempo_days(
                localized_now, start_before_days=364, end_after_days=2
            )
            # Wait depending on last result fetched
            wait_time = self._compute_wait_time(localized_now, end)
            stop = self._stopevent.wait(float(wait_time.seconds))
        # stopping thread
        _LOGGER.info("Thread stopped")

    @callback
    def signalstop(self, event):
        """Activate the stop flag in order to stop the thread from within."""
        _LOGGER.info(
            "Stopping RTE Tempo Calendar API Worker serial thread reader (received %s)",
            event,
        )
        self._stopevent.set()

    def update_options(self, adjusted_days: bool):
        """Setter to update serial reader options."""
        _LOGGER.debug("New adjusted days option value: %s", adjusted_days)
        self.adjusted_days = adjusted_days

    def _compute_wait_time(
        self, localized_now: datetime.datetime, data_end: datetime.datetime | None
    ) -> datetime.timedelta:
        if not data_end:
            # something went wrong, retry in 10 minutes
            return datetime.timedelta(minutes=10)
        # else compute appropriate wait time depending on date_end
        localized_today = datetime.datetime.combine(
            localized_now.date(), datetime.time(tzinfo=FRANCE_TZ)
        )
        diff = data_end - localized_today
        if diff.days == 2:
            # wait until next day
            tomorrow = localized_now + datetime.timedelta(days=1)
            next_call = datetime.datetime(
                year=tomorrow.year,
                month=tomorrow.month,
                day=tomorrow.day,
                tzinfo=localized_now.tzinfo,
            )
            wait_time = next_call - localized_now
            _LOGGER.info(
                "We got next day color, waiting until tomorrow to get futur next day color (wait time is %s)",
                wait_time,
            )
        elif diff.days == 1:
            # we do not have next day color yet
            wait_time = datetime.timedelta(minutes=30)
            _LOGGER.debug(
                "We do not have next day color yet, retrying soon (wait time is %s)",
                wait_time,
            )
        else:
            # weird, should not happen
            wait_time = datetime.timedelta(hours=1)
            _LOGGER.warning(
                "Unexpected delta encountered between today and last result, waiting %s as fallback: %s - %s = %s",
                wait_time,
                data_end,
                localized_today,
                diff,
            )
        # all good
        return wait_time

    def _get_access_token(self):
        _LOGGER.debug("requesting access token")
        self._oauth.fetch_token(token_url=API_TOKEN_ENDPOINT, auth=self._auth)

    def _get_tempo_data(
        self, start: datetime.datetime, end: datetime.datetime
    ) -> Response:
        # prepare params
        start_str = start.strftime(API_DATE_FORMAT)
        end_str = end.strftime(API_DATE_FORMAT)
        params = {
            "start_date": start_str[:-2] + ":" + start_str[-2:],
            "end_date": end_str[:-2] + ":" + end_str[-2:],
        }
        _LOGGER.debug(
            "Calling %s with start_date as '%s' and end_date as '%s'",
            API_TEMPO_ENDPOINT,
            start_str,
            end_str,
        )
        # fetch data
        try:
            return self._oauth.get(
                API_TEMPO_ENDPOINT, params=params, timeout=API_REQ_TIMEOUT
            )
        except TokenExpiredError:
            self._get_access_token()
            return self._oauth.get(
                API_TEMPO_ENDPOINT, params=params, timeout=API_REQ_TIMEOUT
            )

    def _update_tempo_days(
        self, reftime: datetime.datetime, start_before_days: int, end_after_days: int
    ) -> datetime.datetime | None:
        # nullify time but keep date and tz
        localized_date = datetime.datetime.combine(
            reftime.date(), datetime.time(tzinfo=FRANCE_TZ)
        )
        # Get maximum calendar range from current time
        start = localized_date - datetime.timedelta(days=start_before_days)
        end = localized_date + datetime.timedelta(days=end_after_days)
        # Get data
        response = self._get_tempo_data(start, end)
        payload = response.json()
        # Handle API errors
        try:
            error = payload[API_KEY_ERROR]
            error_desc = payload[API_KEY_ERROR_DESC]
            _LOGGER.error("Recovering tempo calendar failed: %s: %s", error, error_desc)
            return None
        except KeyError:
            pass
        # Parse datetimes and fix time for start and end dates
        tempo_days_time: list[TempoDay] = []
        time_days_date: list[TempoDay] = []
        for tempo_day in payload[API_KEY_RESULTS][API_KEY_VALUES]:
            try:
                tempo_days_time.append(
                    TempoDay(
                        Start=adjust_tempo_time(
                            parse_rte_api_datetime(tempo_day[API_KEY_START])
                        ),
                        End=adjust_tempo_time(
                            parse_rte_api_datetime(tempo_day[API_KEY_END])
                        ),
                        Value=tempo_day[API_KEY_VALUE],
                        Updated=parse_rte_api_datetime(tempo_day[API_KEY_UPDATED]),
                    )
                )
                time_days_date.append(
                    TempoDay(
                        Start=parse_rte_api_date(tempo_day[API_KEY_START]),
                        End=parse_rte_api_date(tempo_day[API_KEY_END]),
                        Value=tempo_day[API_KEY_VALUE],
                        Updated=parse_rte_api_datetime(tempo_day[API_KEY_UPDATED]),
                    )
                )
            except KeyError as key_error:
                if tempo_day[API_KEY_START] == "2022-12-28T00:00:00+01:00":
                    # RTE has issued a warning concerning this day missing data on their API: its blue
                    tempo_days_time.append(
                        TempoDay(
                            Start=adjust_tempo_time(
                                parse_rte_api_datetime(tempo_day[API_KEY_START])
                            ),
                            End=adjust_tempo_time(
                                parse_rte_api_datetime(tempo_day[API_KEY_END])
                            ),
                            Value=API_VALUE_BLUE,
                            Updated=parse_rte_api_datetime(tempo_day[API_KEY_UPDATED]),
                        )
                    )
                    time_days_date.append(
                        TempoDay(
                            Start=parse_rte_api_date(tempo_day[API_KEY_START]),
                            End=parse_rte_api_date(tempo_day[API_KEY_END]),
                            Value=API_VALUE_BLUE,
                            Updated=parse_rte_api_datetime(tempo_day[API_KEY_UPDATED]),
                        )
                    )
                else:
                    _LOGGER.warning(
                        "Following day failed to be processed with %s, skipping: %s",
                        repr(key_error),
                        tempo_day,
                    )
        # Save data in memory
        self._tempo_days_time = tempo_days_time
        self._tempo_days_date = time_days_date
        # Return results end date in order for caller to compute next call time
        return parse_rte_api_datetime(payload[API_KEY_RESULTS][API_KEY_END])


def adjust_tempo_time(date: datetime.datetime) -> datetime.datetime:
    """RTE API give midnight to midnight date time while it actually goes from 6 to 6 AM."""
    return date + datetime.timedelta(hours=API_HOUR_OF_CHANGE)


def parse_rte_api_datetime(date: str) -> datetime.datetime:
    """RTE API has a date format incompatible with python parsing."""
    date = (
        date[:-3] + date[-2:]
    )  # switch to a python format (remove ':' from rte tzinfo)
    return datetime.datetime.strptime(date, API_DATE_FORMAT)


def parse_rte_api_date(date: str) -> datetime.date:
    """RTE API has a date format incompatible with python parsing."""
    day_datetime = parse_rte_api_datetime(date)
    return datetime.date(
        year=day_datetime.year, month=day_datetime.month, day=day_datetime.day
    )
