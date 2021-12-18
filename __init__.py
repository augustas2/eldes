"""Support for the Eldes API."""
from datetime import timedelta
import logging
import requests.exceptions

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
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
    DOMAIN,
    SIGNAL_ELDES_UPDATE_RECEIVED
)
from .core.eldes_cloud import EldesCloud

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "switch", "alarm_control_panel"]

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eldes from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    session = async_get_clientsession(hass)
    eldes_client = EldesCloud(session, username, password)

    try:
        await eldes_client.login()
    except Exception as ex:
        _LOGGER.error("Failed to setup eldes: %s", ex)
        return False
    except requests.exceptions.Timeout as ex:
        raise ConfigEntryNotReady from ex
    except requests.exceptions.HTTPError as ex:
        if ex.response.status_code > 400 and ex.response.status_code < 500:
            _LOGGER.error("Failed to login to eldes: %s", ex)
            return False
        raise ConfigEntryNotReady from ex

    async def async_update_data():
        """Fetch data from Eldes API."""
        try:
            devices = await eldes_client.get_devices()

            # Eldes API requires new token before other requests
            await eldes_client.renew_token()

            # Retrieve additional device info, partitions and outputs
            for device in devices:
                device["info"] = await eldes_client.get_device_info(device["imei"])
                device["partitions"] = await eldes_client.get_device_partitions(device["imei"])
                device["outputs"] = await eldes_client.get_device_outputs(device["imei"])

            hass.data[DOMAIN][entry.entry_id][DATA_DEVICES] = devices

            return devices
        except RuntimeError as ex:
            raise ConfigEntryAuthFailed("Not authenticated with Eldes API") from ex
        except Exception as ex:
            _LOGGER.exception(
                "Unknown error occurred during Eldes update request: %s", ex
            )
            raise UpdateFailed(ex) from ex

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=40),
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
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


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
