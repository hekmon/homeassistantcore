"""Constants for the linkytic integration."""

import serial

DOMAIN = "linkytic"


# Config Flow

TICMODE_HISTORIC = "hist"
TICMODE_HISTORIC_LABEL = "Historique"
TICMODE_STANDARD = "std"
TICMODE_STANDARD_LABEL = "Standard"
SETUP_SERIAL = "serial_device"
SETUP_SERIAL_DEFAULT = "/dev/ttyUSB1"
SETUP_TICMODE = "tic_mode"
SETUP_THREEPHASE = "three_phase"
SETUP_THREEPHASE_DEFAULT = False
OPTIONS_REALTIME = "real_time"


# Protocol configuration
#   https://www.enedis.fr/media/2035/download

BYTESIZE = serial.SEVENBITS
PARITY = serial.PARITY_EVEN
STOPBITS = serial.STOPBITS_ONE

MODE_STANDARD_BAUD_RATE = 9600
MODE_STANDARD_FIELD_SEPARATOR = b"\x09"

MODE_HISTORIC_BAUD_RATE = 1200
MODE_HISTORIC_FIELD_SEPARATOR = b"\x20"

LINE_END = b"\r\n"
FRAME_END = b"\r\x03\x02\n"


# Legacy Configuration

SERIAL_READER = "sr"

CONF_SERIAL_PORT = "serial_port"
CONF_STANDARD_MODE = "standard_mode"
CONF_THREE_PHASE = "three-phase"

DEFAULT_SERIAL_PORT = "/dev/ttyUSB0"
DEFAULT_STANDARD_MODE = False
DEFAULT_THREE_PHASE = False
