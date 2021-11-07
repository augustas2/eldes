"""Support for the (unofficial) Eldes API."""
from datetime import timedelta
import logging

import requests.exceptions

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import Throttle

from .const import (
    CONF_FALLBACK,
    DATA,
    DOMAIN,
    SIGNAL_ELDES_UPDATE_RECEIVED,
    UPDATE_LISTENER,
    UPDATE_TRACK,
)

from .core.eldes_cloud import EldesCloud

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "sensor", "alarm_control_panel"]

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)
SCAN_INTERVAL = timedelta(minutes=2)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eldes from a config entry."""

    _async_import_options_from_data_if_missing(hass, entry)

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    fallback = entry.options.get(CONF_FALLBACK, True)

    eldes_connector = EldesConnector(hass, username, password, fallback)

    try:
        await hass.async_add_executor_job(eldes_connector.setup)
    except Exception as exc:
        _LOGGER.error("Failed to setup eldes: %s", exc)
        return False
    except requests.exceptions.Timeout as ex:
        raise ConfigEntryNotReady from ex
    except requests.exceptions.HTTPError as ex:
        if ex.response.status_code > 400 and ex.response.status_code < 500:
            _LOGGER.error("Failed to login to eldes: %s", ex)
            return False
        raise ConfigEntryNotReady from ex

    # Do first update
    await hass.async_add_executor_job(eldes_connector.update)

    # Poll for updates in the background
    update_track = async_track_time_interval(
        hass,
        lambda now: eldes_connector.update(),
        SCAN_INTERVAL,
    )

    update_listener = entry.add_update_listener(_async_update_listener)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA: eldes_connector,
        UPDATE_TRACK: update_track,
        UPDATE_LISTENER: update_listener,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


@callback
def _async_import_options_from_data_if_missing(hass: HomeAssistant, entry: ConfigEntry):
    options = dict(entry.options)
    if CONF_FALLBACK not in options:
        options[CONF_FALLBACK] = entry.data.get(CONF_FALLBACK, True)
        hass.config_entries.async_update_entry(entry, options=options)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hass.data[DOMAIN][entry.entry_id][UPDATE_TRACK]()
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class EldesConnector:
    """An object to store the Eldes data."""

    def __init__(self, hass, username, password, fallback):
        """Initialize Eldes Connector."""
        self.hass = hass
        self._username = username
        self._password = password

        self.home_id = None
        self.home_name = None
        self.eldes = None
        self.devices = None
        self.data = {}

    def setup(self):
        """Connect to Eldes and fetch the devices."""
        self.eldes = EldesCloud(self._username, self._password)

        # Load devices
        devices_response = self.eldes.get_devices()
        devices = devices_response.get("deviceListEntries", [])

        # Renew token before other requests
        self.eldes.renew_token()

        device = devices[0]

        # Retrieve additional device info
        device["info"] = self.eldes.get_device_info(device["imei"])

        self.home_id = device["imei"]
        self.home_name = device["name"]
        self.devices = [device]

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update token to keep session."""
        self.eldes.renew_token()

        """Update the registered devices."""
        for device in self.devices:
            self.update_sensor(device["imei"])

    def update_sensor(self, device_imei):
        """Update the internal data from Eldes."""
        _LOGGER.debug("Updating %s %s", device_imei)
        try:
            info = self.eldes.get_device_info(device_imei)
            partitions = self.eldes.get_device_partitions(device_imei)
            outputs = self.eldes.get_device_outputs(device_imei)
        except RuntimeError:
            _LOGGER.error(
                "Unable to connect to Eldes while updating %s",
                device_imei
            )
            return

        self.data[device_imei] = info
        self.data[device_imei]["partitions"] = partitions.get("partitions", [])
        self.data[device_imei]["outputs"] = outputs.get("deviceOutputs", [])

        _LOGGER.error(self.data[device_imei])

        _LOGGER.debug(
            "Dispatching update to %s %s %s: %s",
            self.home_id,
            device_imei,
            self.data[device_imei],
        )

        dispatcher_send(
            self.hass,
            SIGNAL_ELDES_UPDATE_RECEIVED.format(self.home_id, device_imei),
        )
