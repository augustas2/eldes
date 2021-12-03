"""Support for Eldes sensors."""
import logging

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DATA,
    DOMAIN,
    SIGNAL_ELDES_UPDATE_RECEIVED,
    BINARY_SENSORS
)
from .entity import EldesDeviceEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes binary sensor platform."""
    eldes = hass.data[DOMAIN][entry.entry_id][DATA]
    devices = eldes.devices
    entities = []

    # Create device sensors
    for device in devices:
        entities.extend(
            [
                EldesDeviceBinarySensor(eldes, device, variable)
                for variable in BINARY_SENSORS
            ]
        )

    if entities:
        async_add_entities(entities, True)


class EldesDeviceBinarySensor(EldesDeviceEntity, BinarySensorEntity):
    """Representation of the Eldes binary sensor."""

    def __init__(self, eldes, device_info, device_variable):
        """Initialize of the Eldes binary sensor."""
        self._eldes = eldes
        super().__init__(device_info)

        self.device_variable = device_variable

        self._unique_id = f"{device_variable} {self.device_id} {eldes.home_id}"

        self._state = None

    async def async_added_to_hass(self):
        """Register for sensor updates."""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_ELDES_UPDATE_RECEIVED.format(
                    self._eldes.home_id, self.device_id
                ),
                self._async_update_callback,
            )
        )
        self._async_update_device_data()

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.device_name} {self.device_variable}"

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the class of this sensor."""
        if self.device_variable == "connection status":
            return DEVICE_CLASS_CONNECTIVITY

        return None

    @callback
    def _async_update_callback(self):
        """Update and write state."""
        self._async_update_device_data()
        self.async_write_ha_state()

    @callback
    def _async_update_device_data(self):
        """Handle update callbacks."""
        try:
            self._device_info = self._eldes.data[self.device_id]
        except KeyError:
            return

        if self.device_variable == "connection status":
            self._state = self._device_info.get("online", False)
