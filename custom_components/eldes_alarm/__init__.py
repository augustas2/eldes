"""Support for the Eldes API."""
from datetime import timedelta
import logging
import asyncio
from http import HTTPStatus

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed
)

from .const import (
    DEFAULT_NAME,
    DEFAULT_ZONE,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DATA_DEVICES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_EVENTS_LIST_SIZE,
    CONF_EVENTS_LIST_SIZE,
    DOMAIN
)
from .core.eldes_cloud import EldesCloud

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "switch", "alarm_control_panel"]

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eldes from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    session = async_get_clientsession(hass)
    eldes_client = EldesCloud(session, username, password)

    try:
        await eldes_client.login()
    except (asyncio.TimeoutError, aiohttp.ClientError) as ex:
        if ex.status == HTTPStatus.UNAUTHORIZED:
            raise ConfigEntryAuthFailed from ex

        raise ConfigEntryNotReady from ex
    except Exception as ex:
        _LOGGER.error("Failed to setup Eldes: %s", ex)
        return False

    async def async_update_data():
        try:
            return await async_get_devices(hass, entry, eldes_client)
        except:
            pass

        try:
            await eldes_client.login()
            return await async_get_devices(hass, entry, eldes_client)
        except Exception as ex:
            _LOGGER.exception("Unknown error occurred during Eldes update request: %s", ex)
            raise UpdateFailed(ex) from ex

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: eldes_client,
        DATA_COORDINATOR: coordinator,
        DATA_DEVICES: [],
    }

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    # Setup components
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_get_devices(hass: HomeAssistant, entry: ConfigEntry, eldes_client: EldesCloud):
    """Fetch data from Eldes API."""
    events_list_size = entry.options.get(CONF_EVENTS_LIST_SIZE, DEFAULT_EVENTS_LIST_SIZE)

    await eldes_client.renew_token()

    devices = await eldes_client.get_devices()

    # Retrieve additional device info, partitions and outputs
    for device in devices:
        device["info"] = await eldes_client.get_device_info(device["imei"])
        device["partitions"] = await eldes_client.get_device_partitions(device["imei"])
        device["outputs"] = await eldes_client.get_device_outputs(device["imei"])
        device["temp"] = await eldes_client.get_temperatures(device["imei"])
        device["events"] = await eldes_client.get_events(events_list_size)

    hass.data[DOMAIN][entry.entry_id][DATA_DEVICES] = devices

    return devices


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class EldesDeviceEntity(CoordinatorEntity):
    """Defines a base Eldes device entity."""

    def __init__(self, client, coordinator, device_index, entity_index=None):
        """Initialize the Eldes entity."""
        super().__init__(coordinator)
        self.client = client
        self.device_index = device_index
        self.entity_index = entity_index
        self.imei = self.coordinator.data[self.device_index]["imei"]

    @property
    def data(self):
        """Shortcut to access data for the entity."""
        return self.coordinator.data[self.device_index]

    @property
    def device_info(self):
        """Return device info for the Eldes entity."""
        return {
            "identifiers": {(DOMAIN, self.imei)},
            "name": self.data["info"]["model"],
            "manufacturer": DEFAULT_NAME,
            "sw_version": self.data["info"]["firmware"],
            "model": self.data["info"]["model"]
        }


class EldesZoneEntity(CoordinatorEntity):
    """Defines a base Eldes zone entity."""

    def __init__(self, client, coordinator, device_index, entity_index):
        """Initialize the Eldes entity."""
        super().__init__(coordinator)
        self.client = client
        self.device_index = device_index
        self.entity_index = entity_index
        self.imei = self.coordinator.data[self.device_index]["imei"]

    @property
    def data(self):
        """Shortcut to access data for the entity."""
        return self.coordinator.data[self.device_index]["partitions"][self.entity_index]

    @property
    def device_info(self):
        """Return zone info for the Eldes entity."""
        return {
            "identifiers": {(DOMAIN, self.data["internalId"])},
            "name": self.data["name"],
            "manufacturer": DEFAULT_NAME,
            "model": DEFAULT_ZONE,
            "suggested_area": self.data["name"]
        }
