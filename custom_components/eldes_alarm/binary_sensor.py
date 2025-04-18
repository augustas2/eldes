"""Support for Eldes binary sensors."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
)
from . import EldesDeviceEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes binary sensor platform."""
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = []

    for index, _ in enumerate(coordinator.data):
        entities.append(EldesConnectionStatusBinarySensor(client, coordinator, index))

    async_add_entities(entities)


class EldesConnectionStatusBinarySensor(EldesDeviceEntity, BinarySensorEntity):
    """Class for the Eldes connection status sensor."""

    @property
    def unique_id(self):
        return f"{self.imei}_connection_status"

    @property
    def name(self):
        return f"{self.data["info"]["model"]} Connection Status"

    @property
    def is_on(self):
        return self.data["info"].get("online", False)

    @property
    def device_class(self):
        return BinarySensorDeviceClass.CONNECTIVITY
