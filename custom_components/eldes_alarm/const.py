"""Constant values for the Eldes component."""

DOMAIN = "eldes_alarm"
DEFAULT_NAME = "Eldes"

DATA_CLIENT = "eldes_client"
DATA_COORDINATOR = "coordinator"
CONF_DEVICE_IMEI = "device_imei"
CONF_EVENTS_LIST_SIZE = "events_list_size"
SCAN_INTERVAL_MIN = 10
SCAN_INTERVAL_MAX = 300
EVENTS_LIST_SIZE_MIN = 5
EVENTS_LIST_SIZE_MAX = 50

DEFAULT_SCAN_INTERVAL = 30
DEFAULT_EVENTS_LIST_SIZE = 10
DEFAULT_OUTPUT_ICON = "ICON_1"

API_URL = "https://cloud.eldesalarms.com:8083/api/"

API_PATHS = {
    "AUTH": "auth/",
    "DEVICE": "device/",
}

ALARM_MODES = {
    "DISARM": "disarm",
    "ARM_AWAY": "arm",
    "ARM_HOME": "armstay",
}

OUTPUT_TYPES = {
    "SWITCH": "SWITCH",
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
    4: 100,
}

BATTERY_STATUS_MAP = {
    True: "OK",
    False: "Bad",
}

ATTR_EVENTS = "events"
ATTR_ALARMS = "alarms"
ATTR_USER_ACTIONS = "user_actions"

EVENT_TYPE_ALARM = "ALARM"
EVENT_TYPE_ARM = "ARM"
EVENT_TYPE_DISARM = "DISARM"

