"""Support for Eldes sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, DEVICE_CLASS_TEMPERATURE

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
        entities.append(EldesPhoneNumberSensor(client, coordinator, index))
        for tempIndex, _ in enumerate(coordinator.data[index]["temp"]):
            entities.append(EldesTemperatureSensor(client, coordinator, index, tempIndex))

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


class EldesPhoneNumberSensor(EldesDeviceEntity, SensorEntity):
    """Class for the phone number sensor."""

    @property
    def unique_id(self):
        """Return a unique identifier for this entity."""
        return f"{self.imei}_phone_number"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.data['info']['model']} Phone Number"

    @property
    def icon(self):
        """Return the icon of this sensor."""
        return "mdi:cellphone"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.data["info"].get("phoneNumber", "")


class EldesTemperatureSensor(EldesDeviceEntity, SensorEntity):
    """Class for the temperature sensor."""

    @property
    def unique_id(self):
        """Return a unique identifier for this entity."""
        return f"{self.imei}_{self.__get_temp()['sensorName']}_{self.__get_temp()['sensorId']}_temperature"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.__get_temp()['sensorName']} Temperature"

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_TEMPERATURE

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def native_value(self):
        """Return the value of the sensor."""
        return self.__get_temp().get("temperature", 0.0)

    def __get_temp(self):
        """Return sensor data."""
        return self.data["temp"][self.entity_index]
