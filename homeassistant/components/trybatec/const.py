"""Constants for the Trybatec integration."""
from zoneinfo import ZoneInfo

DOMAIN = "trybatec"

# Config Flow
CONFIG_USERNAME = "username"
CONFIG_PASSWORD = "password"

# API
TRYBATEC_API_DOMAIN = "portail.trybatec.fr"
USER_AGENT = "github.com/hekmon/ha-trybatec"
FRANCE_TZ = ZoneInfo("Europe/Paris")
DEVICE_PAYLOAD_ID = "id"
DEVICE_PAYLOAD_NAME = "fluid"
DEVICE_PAYLOAD_NAME_CODE = "fluidCode"
DEVICE_PAYLOAD_NAME_CODE_COLDWATER = "EF"
DEVICE_PAYLOAD_NAME_CODE_HOTWATER = "ECS"
DEVICE_PAYLOAD_NAME_CODE_HEAT = "CET"
DEVICE_PAYLOAD_LOCALISATION = "name"
DEVICE_PAYLOAD_RESIDENCE = "deal"
DEVICE_PAYLOAD_SHARE = "lot"
DEVICE_PAYLOAD_STATE = "state"
DEVICE_PAYLOAD_TYPE = "type"
DEVICE_PAYLOAD_SN = "serialNumber"
DEVICE_PAYLOAD_EMIT_SN = "emetSerialNumber"
DEVICE_PAYLOAD_ACTIVATION_DATE = "validFrom"
DEVICE_PAYLOAD_PICTURE = "picture"
