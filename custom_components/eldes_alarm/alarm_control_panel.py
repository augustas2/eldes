"""Interfaces with Eldes control panels."""
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    ALARM_MODES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes alarm control panel platform."""
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = []

    for device_index, device in enumerate(coordinator.data):
        for partition_index, _ in enumerate(device["partitions"]):
            entities.append(EldesAlarmPanel(client, coordinator, device_index, partition_index))

    async_add_entities(entities)


class EldesAlarmPanel(CoordinatorEntity, AlarmControlPanelEntity):
    """Representation of an Eldes Alarm."""

    _attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_HOME
    )
    _attr_code_arm_required = False

    def __init__(self, client, coordinator, device_index, partition_index):
        super().__init__(coordinator)
        self.client = client
        self.device_index = device_index
        self.partition_index = partition_index

    @property
    def imei(self):
        return self.coordinator.data[self.device_index].get("imei")

    @property
    def data(self):
        return self.coordinator.data[self.device_index]["partitions"][self.partition_index]

    @property
    def unique_id(self):
        return f"{self.imei}_zone_{self.data['internalId']}"

    @property
    def name(self):
        return self.data["name"]

    @property
    def state(self):
        return self.data["state"]

    @property
    def extra_state_attributes(self):
        return {
            "armed": self.data["armed"],
            "armStay": self.data["armStay"],
            "state": self.data["state"],
            "hasUnacceptedPartitionAlarms": self.data["hasUnacceptedPartitionAlarms"],
        }

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        current_state = self.state
        self.data["state"] = AlarmControlPanelState.DISARMING
        self.async_write_ha_state()

        try:
            await self.client.renew_token()
            await self.client.set_alarm(
                ALARM_MODES["DISARM"],
                self.imei,
                self.data['internalId']
            )
        except Exception as ex:
            _LOGGER.error("Failed to change state: %s", ex)
            self.data["state"] = current_state
            self.async_write_ha_state()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        current_state = self.state
        self.data["state"] = AlarmControlPanelState.ARMING
        self.async_write_ha_state()

        try:
            await self.client.renew_token()
            await self.client.set_alarm(
                ALARM_MODES["ARM_AWAY"],
                self.imei,
                self.data['internalId']
            )
        except Exception as ex:
            _LOGGER.error("Failed to change state: %s", ex)
            self.data["state"] = current_state
            self.async_write_ha_state()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        current_state = self.state
        self.data["state"] = AlarmControlPanelState.ARMING
        self.async_write_ha_state()

        try:
            await self.client.renew_token()
            await self.client.set_alarm(
                ALARM_MODES["ARM_HOME"],
                self.imei,
                self.data['internalId']
            )
        except Exception as ex:
            _LOGGER.error("Failed to change state: %s", ex)
            self.data["state"] = current_state
            self.async_write_ha_state()
