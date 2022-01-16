"""Constant values for the Eldes component."""

DOMAIN = "eldes"
DEFAULT_NAME = "Eldes"
DEFAULT_ZONE = "Zone"

DATA_CLIENT = "eldes_client"
DATA_COORDINATOR = "coordinator"
DATA_DEVICES = "devices"

API_URL = "https://cloud.eldesalarms.com:8083/api/"

API_PATHS = {
    "AUTH": "auth/",
    "DEVICE": "device/"
}

ALARM_MODES = {
    "DISARM": "disarm",
    "ARM_AWAY": "arm",
    "ARM_HOME": "armstay"
}

OUTPUT_TYPES = {
    "SWITCH": "SWITCH"
}

OUTPUT_ICONS_MAP = {
    "ICON_0": "mdi:fan",
    "ICON_1": "mdi:lightning-bolt-outline",
    "ICON_2": "mdi:power-socket-eu",
    "ICON_3": "mdi:power-plug",
}

SIGNAL_STRENGTH_MAP = {
    0: 0,
    1: 30,
    2: 60,
    3: 80,
    4: 100
}

BATTERY_STATUS_MAP = {
    True: "OK",
    False: "Bad"
}
