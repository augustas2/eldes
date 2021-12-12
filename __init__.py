"""Support for the Eldes API."""
from datetime import timedelta
import logging
import requests.exceptions
from aiohttp import ClientSession

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import (
    DATA,
    DOMAIN,
    SIGNAL_ELDES_UPDATE_RECEIVED,
    UPDATE_LISTENER,
    UPDATE_TRACK,
)
from .core.eldes_cloud import EldesCloud

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "sensor", "alarm_control_panel", "switch"]

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)
SCAN_INTERVAL = timedelta(minutes=1)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eldes from a config entry."""

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    session = async_get_clientsession(hass)

    eldes_connector = EldesConnector(hass, session, username, password)

    try:
        await eldes_connector.setup()
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
    await eldes_connector.update()

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

    def __init__(self, hass: HomeAssistant, session: ClientSession, username: str, password: str):
        """Initialize Eldes Connector."""
        self.hass = hass
        self._session = session
        self._username = username
        self._password = password

        self.home_id = None
        self.home_name = None
        self.eldes = None
        self.devices = None
        self.data = {}

    async def setup(self):
        """Connect to Eldes and fetch data."""
        self.eldes = EldesCloud(self._session)

        # Login to Eldes
        await self.eldes.login(self._username, self._password)

        # Load devices
        devices_response = await self.eldes.get_devices()
        devices = devices_response.get("deviceListEntries", [])

        # Renew token before other requests
        await self.eldes.renew_token()

        device = devices[0]

        # Retrieve additional device data
        device["info"] = await self.eldes.get_device_info(device["imei"])

        partitions_response = await self.eldes.get_device_partitions(device["imei"])
        device["partitions"] = partitions_response.get("partitions", [])

        outputs_response = await self.eldes.get_device_outputs(device["imei"])
        device["outputs"] = outputs_response.get("deviceOutputs", [])

        self.home_id = device["imei"]
        self.home_name = device["name"]
        self.devices = [device]

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update(self):
        """Update token to keep session."""
        await self.eldes.renew_token()

        """Update the registered devices."""
        for device in self.devices:
            await self.update_sensor(device["imei"])

    async def update_sensor(self, device_imei):
        """Update the internal data from Eldes."""
        _LOGGER.debug("Updating %s", device_imei)

        try:
            info = await self.eldes.get_device_info(device_imei)
            partitions = await self.eldes.get_device_partitions(device_imei)
            outputs = await self.eldes.get_device_outputs(device_imei)

            self.data[device_imei] = info
            self.data[device_imei]["partitions"] = partitions.get("partitions", [])
            self.data[device_imei]["outputs"] = outputs.get("deviceOutputs", [])

            _LOGGER.debug(
                "Dispatching update to %s %s: %s",
                self.home_id,
                device_imei,
                self.data[device_imei],
            )

            _LOGGER.error(self.data[device_imei])

            dispatcher_send(
                self.hass,
                SIGNAL_ELDES_UPDATE_RECEIVED.format(self.home_id, device_imei),
            )
        except RuntimeError:
            _LOGGER.error(
                "Unable to connect to Eldes while updating %s",
                device_imei
            )
            pass
