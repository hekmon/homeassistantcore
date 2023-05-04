# pylint: disable=broad-exception-caught
"""Trybatec API controllers and helpers."""
from __future__ import annotations

import base64
import datetime
import json
import logging
import string

import aiohttp

from homeassistant.core import Event

from .const import FRANCE_TZ, TRYBATEC_API_DOMAIN, USER_AGENT
from .tlsfix import TrybatecBadTLS

_LOGGER = logging.getLogger(__name__)


class APIError(Exception):
    """Generic API error."""

    def __init__(self, *args: object) -> None:
        """Initialize API Error."""
        super().__init__(*args)


class TrybatecAPI:
    """Trybatec API controller."""

    def __init__(
        self, session: aiohttp.ClientSession, username: str, password: str
    ) -> None:
        """Init trybatec async API controller."""
        # Persistent
        self.username = username
        self.password = password
        self.websession = session
        # Shitty web server TLS config
        self.sslhelper = TrybatecBadTLS()
        _LOGGER.debug(
            "custom CA store with missing intermediate certificate injected created at %s",
            self.sslhelper.custom_store_path,
        )
        # State
        self.housing_id: str | None = None
        self.token: str | None = None
        self.token_expire: datetime.datetime | None = None

    async def _login(self) -> None:
        async with self.websession.post(
            f"https://{TRYBATEC_API_DOMAIN}/api/v1/authenticate",
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            json={
                "username": self.username,
                "password": self.password,
            },
            ssl=self.sslhelper.ssl_ctx,
        ) as resp:
            assert (
                resp.status == 200
            ), f"authentication failed with status code {resp.status}"
            # Extract information we need from response payload
            response_payload = await resp.json()
            try:
                self.housing_id = response_payload["housingId"]
                self.token = str(response_payload["token"])
                # Extract excire time from token
                token_infos_b64 = self.token.split(".")[1]
                token_infos_json = base64.b64decode(token_infos_b64)
                token_infos = json.loads(token_infos_json)
                token_expire_timestamp = token_infos["exp"]
                self.token_expire = datetime.datetime.fromtimestamp(
                    token_expire_timestamp, tz=datetime.timezone.utc
                )
            except (KeyError, IndexError) as exc:
                self.housing_id = None
                self.token = None
                self.token_expire = None
                raise APIError(
                    f"extracting logging information from authentication response payload failed with index or key error: {exc}"
                ) from exc

    async def _refresh_token(self) -> None:
        """Check auth token validity and reauth if necessary."""
        # In case this is the first connection
        if self.token_expire is None:
            await self._login()
            return
        # In case our auth token has excired
        localized_now = datetime.datetime.now(FRANCE_TZ)
        if localized_now > self.token_expire:
            await self._login()
            return
        # Token still valid
        return

    def cleanup(self, event: Event):
        """Properly stop the controller."""
        _LOGGER.debug("received event %s: cleaning up custom local CA store", event)
        self.sslhelper.cleanup()

    async def get_devices(self) -> dict:
        """Return available devices."""
        try:
            # Make sure we have an auth token
            await self._refresh_token()
            # Get devices from API
            async with self.websession.get(
                f"https://{TRYBATEC_API_DOMAIN}/api/v1/devices",
                params={"housingId": self.housing_id},
                headers={
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                    "Authorization": f"Bearer {self.token}",
                },
                ssl=self.sslhelper.ssl_ctx,
            ) as resp:
                assert (
                    resp.status == 200
                ), f"getting devices failed with status code {resp.status}"
                return await resp.json()
        except Exception as exc:
            raise APIError(f"devices API request failed: {exc}") from exc

    async def get_data(self, device_id: str, fluid_id: int) -> list:
        """Get last 24h data for a particular device."""
        try:
            # Make sure we have an auth token
            await self._refresh_token()
            # Compute data window
            today = datetime.datetime.now(tz=FRANCE_TZ)
            yesterday = today - datetime.timedelta(days=1)
            # Get devices from API
            async with self.websession.get(
                f"https://{TRYBATEC_API_DOMAIN}/api/v1/consumption",
                params={
                    "deviceId": device_id,
                    "groupBy": "D",  # ??
                    "fluidId": fluid_id,
                    "start": yesterday.strftime("%Y-%m-%d"),
                    "end": today.strftime("%Y-%m-%d"),
                },
                headers={
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                    "Authorization": f"Bearer {self.token}",
                },
                ssl=self.sslhelper.ssl_ctx,
            ) as resp:
                assert (
                    resp.status == 200
                ), f"getting consumption failed with status code {resp.status}"
                return await resp.json()
        except Exception as exc:
            raise APIError(f"consumption data API request failed: {exc}") from exc

    async def test_login(self) -> None:
        """Test if login with provided credentials works."""
        try:
            await self._refresh_token()
        except Exception as exc:
            raise APIError(f"login failed: {exc}") from exc


def generate_entity_picture(picture: str) -> str:
    """Generate full URL from device picture."""
    return f"https://{TRYBATEC_API_DOMAIN}/image/devices/{picture}"


def parse_iso_date(date: str) -> datetime.datetime:
    """Parse API ISO datetime as python datetime."""
    return datetime.datetime.fromisoformat(date).astimezone(FRANCE_TZ)


def cleanup_str(field: str) -> str:
    """Cleanup some str fields from API."""
    return string.capwords(field.lower().rstrip().lstrip())
