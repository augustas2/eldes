"""Constant values for the Eldes component."""

# General
DOMAIN = "eldes"
DEFAULT_NAME = "Eldes"
DEFAULT_ZONE = "Zone"

SIGNAL_ELDES_UPDATE_RECEIVED = "eldes_update_received_{}_{}"
UPDATE_LISTENER = "update_listener"
DATA = "data"
UPDATE_TRACK = "update_track"
UNIQUE_ID = "unique_id"

# API
API_URL = "https://cloud.eldesalarms.com:8083/api/"

# Endpoints
API_PATHS = {
    "AUTH": "auth/",
    "DEVICE": "device/"
}

# Alarm modes
ALARM_MODES = {
    "DISARM": "disarm",
    "ARM_AWAY": "arm",
    "ARM_HOME": "armstay"
}

# Output types
OUTPUT_TYPES = {
    "SWITCH": "SWITCH"
}

OUTPUT_ICONS_MAP = {
    "ICON_0": "mdi:fan",
    "ICON_1": "mdi:lightning-bolt-outline",
    "ICON_2": "mdi:power-socket-eu",
    "ICON_3": "mdi:power-plug",
}

BINARY_SENSORS = [
    "connection status"
]

SENSORS = [
    "battery status",
    "GSM strength",
    "phone number",
    "view cameras allowed"
]

SIGNAL_STRENGTH_MAP = {
    0: 0,
    1: 30,
    2: 60,
    3: 80,
    4: 100
}

BOOLEAN_MAP = {
    True: "Yes",
    False: "No"
}

BATTERY_STATUS_MAP = {
    True: "OK",
    False: "Bad"
}
