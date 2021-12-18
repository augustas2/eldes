"""Support for Eldes sensors."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    OUTPUT_ICONS_MAP
)
from . import EldesDeviceEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes sensor platform."""
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = []

    for deviceIndex, _ in enumerate(coordinator.data):
        for outputIndex, _ in enumerate(coordinator.data[deviceIndex]["outputs"]):
            entities.append(EldesSwitch(client, coordinator, deviceIndex, outputIndex))

    async_add_entities(entities)


class EldesSwitch(EldesDeviceEntity, SwitchEntity):
    """Class for the battery status sensor."""

    @property
    def unique_id(self):
        """Return a unique identifier for this entity."""
        return f"{self.imei}_output_{self.data['outputs'][self.entity_index]['id']}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.data['outputs'][self.entity_index]['name']

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.data["outputs"][self.entity_index].get("outputState", False)

    @property
    def icon(self):
        """Return the icon of this sensor."""
        return OUTPUT_ICONS_MAP[self.data["outputs"][self.entity_index].get("iconName", "ICON_1")]

    async def async_turn_on(self):
        """Turn the entity on."""
        await self.client.turn_on_output(
            self.imei,
            self.entity_index
        )

        self.data["outputs"][self.entity_index]["outputState"] = True
        self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn the entity off."""
        await self.client.turn_off_output(
            self.imei,
            self.entity_index
        )

        self.data["outputs"][self.entity_index]["outputState"] = False
        self.async_write_ha_state()
