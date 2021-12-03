"""Support for Eldes sensors."""
import logging

from homeassistant.components.sensor import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DATA, DOMAIN, SIGNAL_ELDES_UPDATE_RECEIVED, OUTPUT_TYPES, OUTPUT_ICONS_MAP
from .entity import EldesDeviceEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes sensor platform."""
    eldes = hass.data[DOMAIN][entry.entry_id][DATA]
    devices = eldes.devices
    entities = []

    # Create switches
    for device in devices:
        entities.extend(
            [
                EldesSwitch(eldes, output, device)
                for output in device["outputs"] if output.type == OUTPUT_TYPES.SWITCH
            ]
        )

    if entities:
        async_add_entities(entities, True)


class EldesSwitch(EldesDeviceEntity, SwitchEntity):
    """Representation of the Eldes switch."""

    def __init__(self, eldes, output, device_variable):
        """Initialize of the Eldes switch."""
        super().__init__(output)
        self._eldes = eldes

        self.device_variable = device_variable

        self._unique_id = f"{device_variable} {self.device_id} {eldes.home_id}"

        self._state = None

    async def async_added_to_hass(self):
        """Register for output updates."""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_ELDES_UPDATE_RECEIVED.format(
                    self._eldes.home_id, self.device_id
                ),
                self._async_update_callback,
            )
        )
        self._async_update_output_data()

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the output."""
        return f"{self.device_name} {self.device_variable}"

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    """@property
    def icon(self):
        Return the icon of this sensor.
        try:
            self._device_info = self._eldes.data[self.device_id]
        except KeyError:
            return

        if self.device_variable == "phone number":
            return "mdi:cellphone"

        if self.device_variable == "view cameras allowed":
            return "mdi:cctv"

        return None"""

    @callback
    def _async_update_callback(self):
        """Update and write state."""
        self._async_update_output_data()
        self.async_write_ha_state()

    @callback
    def _async_update_output_data(self):
        """Handle update callbacks."""
        self._output_info = next(
            (
                output for output in self._eldes.data[self.device_id]["outputs"]
                if output["id"] == self.output_id
            ), None
        )

        if self._output_info is not None:
            self._state = self._output_info.get("outputState", False)
