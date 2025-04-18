"""Support for Eldes switches."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    OUTPUT_ICONS_MAP,
    DEFAULT_OUTPUT_ICON,
)
from . import EldesDeviceEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes switch platform."""
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = []

    for device_index, _ in enumerate(coordinator.data):
        for output_index, _ in enumerate(coordinator.data[device_index]["outputs"]):
            entities.append(EldesSwitch(client, coordinator, device_index, output_index))

    async_add_entities(entities)


class EldesSwitch(EldesDeviceEntity, SwitchEntity):
    """Representation of an Eldes output switch."""

    @property
    def output(self):
        return self.data["outputs"][self.entity_index]

    @property
    def unique_id(self):
        return f"{self.imei}_output_{self.output["id"]}"

    @property
    def name(self):
        return self.output["name"]

    @property
    def is_on(self):
        return self.output.get("outputState", False)

    @property
    def extra_state_attributes(self):
        return {
            "hasFault": self.output["hasFault"],
            "outputState": self.output["outputState"],
            "type": self.output["type"]
        }

    @property
    def icon(self):
        icon_name = self.output.get("iconName", DEFAULT_OUTPUT_ICON)
        return OUTPUT_ICONS_MAP.get(icon_name, OUTPUT_ICONS_MAP[DEFAULT_OUTPUT_ICON])

    async def async_turn_on(self):
        await self.client.turn_on_output(
            self.imei,
            self.output["id"]
        )

        self.output["outputState"] = True
        self.async_write_ha_state()

    async def async_turn_off(self):
        await self.client.turn_off_output(
            self.imei,
            self.output["id"]
        )

        self.output["outputState"] = False
        self.async_write_ha_state()
