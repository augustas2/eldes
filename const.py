"""Constant values for the Eldes component."""

# General
DOMAIN = "eldes"
DEFAULT_NAME = "Eldes"
DEFAULT_ZONE = "Zone"

SIGNAL_ELDES_UPDATE_RECEIVED = "eldes_update_received_{}_{}"
UPDATE_LISTENER = "update_listener"
CONF_FALLBACK = "fallback"
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
