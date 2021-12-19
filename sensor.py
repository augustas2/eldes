"""Support for Eldes sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import PERCENTAGE

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    SIGNAL_STRENGTH_MAP,
    BATTERY_STATUS_MAP
)
from . import EldesDeviceEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes sensor platform."""
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = []

    for index, _ in enumerate(coordinator.data):
        entities.append(EldesBatteryStatusSensor(client, coordinator, index))
        entities.append(EldesGSMStrengthSensor(client, coordinator, index))

    async_add_entities(entities)


class EldesBatteryStatusSensor(EldesDeviceEntity, SensorEntity):
    """Class for the battery status sensor."""

    @property
    def unique_id(self):
        """Return a unique identifier for this entity."""
        return f"{self.imei}_battery_status"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.data['info']['model']} Battery Status"

    @property
    def icon(self):
        """Return the icon of this sensor."""
        if not self.data["info"]["batteryStatus"]:
            return "mdi:battery-alert-variant-outline"
        return "mdi:battery"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return BATTERY_STATUS_MAP[self.data["info"].get("batteryStatus", False)]


class EldesGSMStrengthSensor(EldesDeviceEntity, SensorEntity):
    """Class for the GSM strength sensor."""

    @property
    def unique_id(self):
        """Return a unique identifier for this entity."""
        return f"{self.imei}_gsm_strength"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.data['info']['model']} GSM Strength"

    @property
    def icon(self):
        """Return the icon of this sensor."""
        if self.data["info"]["gsmStrength"] == 0:
            return "mdi:signal-off"
        return "mdi:signal"

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return PERCENTAGE

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return SIGNAL_STRENGTH_MAP[self.data["info"].get("gsmStrength", 0)]
