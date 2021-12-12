"""Support for Eldes sensors."""
import logging

from homeassistant.components.switch import SwitchEntity
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
    try:
        for device in devices:
            if "outputs" in device:
                for output in device["outputs"]:
                    if output["type"] == OUTPUT_TYPES["SWITCH"]:
                        entities.extend(
                            [
                                EldesSwitch(eldes, device, output)
                            ]
                        )
    except KeyError:
        pass

    if entities:
        async_add_entities(entities, True)


class EldesSwitch(EldesDeviceEntity, SwitchEntity):
    """Representation of the Eldes switch."""

    def __init__(self, eldes, device, output):
        """Initialize of the Eldes switch."""
        super().__init__(device)
        self._eldes = eldes

        self._output_id = output["id"]
        self._output_name = output["name"]
        self._unique_id = f"{output['id']} {eldes.home_id}"
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
        return self._output_name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    @property
    def icon(self):
        """Return the icon of this switch."""
        try:
            output_info = next(
                (
                    output for output in self._eldes.data[self.device_id]["outputs"]
                    if output["id"] == self._output_id
                ), None
            )

            if output_info is not None:
                return OUTPUT_ICONS_MAP[output_info.get("iconName"), "ICON_1"]

        except KeyError:
            pass

        return None

    async def async_turn_on(self):
        """Turn the entity on."""
        try:
            await self._eldes.eldes.turn_on_output(
                self.device_id,
                self._output_id
            )
        except Exception as err:
            _LOGGER.error('Error while turning on %s: %s', self._output_name, err)
            return

        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn the entity off."""
        try:
            await self._eldes.eldes.turn_off_output(
                self.device_id,
                self._output_id
            )
        except Exception as err:
            _LOGGER.error('Error while turning off %s: %s', self._output_name, err)
            return

        self._state = False
        self.async_write_ha_state()

    @callback
    def _async_update_callback(self):
        """Update and write state."""
        self._async_update_output_data()
        self.async_write_ha_state()

    @callback
    def _async_update_output_data(self):
        """Handle update callbacks."""
        try:
            output_info = next(
                (
                    output for output in self._eldes.data[self.device_id]["outputs"]
                    if output["id"] == self._output_id
                ), None
            )

            if output_info is not None:
                self._state = output_info.get("outputState", False)
        except KeyError:
            pass
