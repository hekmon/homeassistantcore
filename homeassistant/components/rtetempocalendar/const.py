"""Constants for the RTE Tempo Calendar integration."""
from zoneinfo import ZoneInfo

DOMAIN = "rtetempocalendar"


# Config Flow

CONFIG_CLIENT_ID = "client_id"
CONFIG_CLIEND_SECRET = "client_secret"


# Device

DEVICE_NAME = "RTE Tempo"
DEVICE_MANUFACTURER = "RTE"
DEVICE_MODEL = "Calendrier Tempo"


# API Worker

FRANCE_TZ = ZoneInfo("Europe/Paris")
API_DOMAIN = "https://digital.iservices.rte-france.com"
API_TOKEN_ENDPOINT = f"{API_DOMAIN}/token/oauth"
API_TEMPO_ENDPOINT = (
    f"{API_DOMAIN}/open_api/tempo_like_supply_contract/v1/tempo_like_calendars"
)
API_REQ_TIMEOUT = 3
API_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
API_KEY_ERROR = "error"
API_KEY_ERROR_DESC = "error_description"
API_KEY_RESULTS = "tempo_like_calendars"
API_KEY_VALUES = "values"
API_KEY_START = "start_date"
API_KEY_END = "end_date"
API_KEY_VALUE = "value"
API_KEY_UPDATED = "updated_date"
API_VALUE_RED = "RED"
API_VALUE_WHITE = "WHITE"
API_VALUE_BLUE = "BLUE"
