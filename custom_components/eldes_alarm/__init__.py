"""Support for the Eldes API."""
from datetime import timedelta
import logging
import asyncio
from http import HTTPStatus

from aiohttp import ClientResponseError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
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
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    CONF_DEVICE_IMEI,
    CONF_EVENTS_LIST_SIZE,
    DEFAULT_EVENTS_LIST_SIZE,
    DOMAIN,
)

from .core.eldes_cloud import EldesCloud

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "switch", "alarm_control_panel"]

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eldes from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    selected_imei = entry.data[CONF_DEVICE_IMEI]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    session = async_get_clientsession(hass)
    eldes_client = EldesCloud(session, username, password)

    try:
        await eldes_client.login()
    except (asyncio.TimeoutError, ClientResponseError) as ex:
        if isinstance(ex, ClientResponseError) and ex.status == HTTPStatus.UNAUTHORIZED:
            raise ConfigEntryAuthFailed from ex
        raise ConfigEntryNotReady from ex
    except Exception as ex:
        _LOGGER.error("Failed to login to Eldes: %s", ex)
        return False

    async def async_update_data():
        """Fetch data for selected Eldes device."""
        try:
            await eldes_client.renew_token()
            return [await async_fetch_device_data(eldes_client, selected_imei, entry)]
        except Exception as ex:
            _LOGGER.exception("Failed to update Eldes device data: %s", ex)
            raise UpdateFailed(ex) from ex

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"Eldes {selected_imei}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: eldes_client,
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_fetch_device_data(eldes_client: EldesCloud, imei: str, entry: ConfigEntry) -> dict:
    """Fetch full data for a single Eldes device."""
    events_list_size = entry.options.get(CONF_EVENTS_LIST_SIZE, DEFAULT_EVENTS_LIST_SIZE)

    device = {
        "imei": imei,
        "info": await eldes_client.get_device_info(imei),
        "partitions": await eldes_client.get_device_partitions(imei),
        "outputs": await eldes_client.get_device_outputs(imei),
        "temp": await eldes_client.get_temperatures(imei),
        "events": await eldes_client.get_events(imei, events_list_size),
    }

    return device


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Eldes config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
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
        """Shortcut to access this device's data."""
        return self.coordinator.data[self.device_index]

    @property
    def device_info(self):
        """Return device info for the Eldes entity."""
        return {
            "identifiers": {(DOMAIN, self.imei)},
            "name": self.data["info"]["model"],
            "manufacturer": DEFAULT_NAME,
            "sw_version": self.data["info"]["firmware"],
            "model": self.data["info"]["model"],
        }
