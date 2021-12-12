"""Support for Eldes sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DATA,
    DOMAIN,
    SIGNAL_ELDES_UPDATE_RECEIVED,
    DEVICE_SENSORS,
    SIGNAL_STRENGTH_MAP,
    BOOLEAN_MAP,
    BATTERY_STATUS_MAP
)
from .entity import EldesDeviceEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes sensor platform."""
    eldes = hass.data[DOMAIN][entry.entry_id][DATA]
    devices = eldes.devices
    entities = []

    # Create device & zone sensors
    try:
        for device in devices:
            entities.extend(
                [
                    EldesDeviceSensor(eldes, device, variable)
                    for variable in DEVICE_SENSORS
                ]
            )
    except KeyError:
        pass

    if entities:
        async_add_entities(entities, True)


class EldesDeviceSensor(EldesDeviceEntity, SensorEntity):
    """Representation of the Eldes sensor."""

    def __init__(self, eldes, device, device_variable):
        """Initialize of the Eldes sensor."""
        super().__init__(device)
        self._eldes = eldes

        self.device_variable = device_variable
        self._unique_id = f"{device_variable} {self.device_id} {eldes.home_id}"
        self._state_attributes = None
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
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        if self.device_variable == "GSM strength":
            return "%"

        return None

    @property
    def device_class(self):
        """Return the device class."""
        return None

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._state_attributes

    @property
    def icon(self):
        """Return the icon of this sensor."""
        try:
            self._device_info = self._eldes.data[self.device_id]
        except KeyError:
            return

        if self.device_variable == "GSM strength":
            if self._device_info["gsmStrength"] == 0:
                return "mdi:signal-off"
            return "mdi:signal"

        if self.device_variable == "battery status":
            if not self._device_info["batteryStatus"]:
                return "mdi:battery-alert-variant-outline"
            return "mdi:battery"

        if self.device_variable == "phone number":
            return "mdi:cellphone"

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
            device_info = self._eldes.data[self.device_id]
        except KeyError:
            return

        if self.device_variable == "battery status":
            self._state = BATTERY_STATUS_MAP[device_info.get("batteryStatus", False)]
        elif self.device_variable == "GSM strength":
            self._state = SIGNAL_STRENGTH_MAP[device_info.get("gsmStrength", 0)]
        elif self.device_variable == "phone number":
            self._state = device_info.get("phoneNumber", "")

        self._state_attributes = {
            "status": device_info.get("status", "SUCCESS"),
            "migrationPending": device_info.get("migrationPending", False),
            "viewCamerasAllowed": device_info.get("viewCamerasAllowed", False)
        }
