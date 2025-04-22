"""Support for Eldes control panels."""
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
from . import EldesDeviceEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes alarm control panel platform."""
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = []

    for device_index, device in enumerate(coordinator.data):
        for partition_index in range(len(device["partitions"])):
            entity = EldesAlarmPanel(client, coordinator, device_index, partition_index)
            entity._attr_alarm_state = entity.partition["state"]
            entities.append(entity)

    async_add_entities(entities)


class EldesAlarmPanel(EldesDeviceEntity, AlarmControlPanelEntity):
    """Class for the Eldes alarm control panel."""

    _attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_HOME
    )
    _attr_code_arm_required = False

    def __init__(self, client, coordinator, device_index, partition_index):
        super().__init__(client, coordinator, device_index, partition_index)
        self._attr_alarm_state = None

    @property
    def partition(self):
        return self.data["partitions"][self.entity_index]

    @property
    def unique_id(self):
        return f"{self.imei}_zone_{self.partition['internalId']}"

    @property
    def name(self):
        return self.partition["name"]

    @property
    def extra_state_attributes(self):
        return {
            "armed": self.partition["armed"],
            "armStay": self.partition["armStay"],
            "state": self.partition["state"],
            "hasUnacceptedPartitionAlarms": self.partition["hasUnacceptedPartitionAlarms"],
        }

    def _handle_coordinator_update(self) -> None:
        """Update the state when coordinator provides new data."""
        self._attr_alarm_state = self.partition["state"]
        self.async_write_ha_state()

    async def _async_set_alarm(self, mode: str, target_state: AlarmControlPanelState, transition_state: AlarmControlPanelState) -> None:
        previous_state = self._attr_alarm_state
        self._attr_alarm_state = transition_state
        self.async_write_ha_state()

        try:
            await self.client.renew_token()
            await self.client.set_alarm(mode, self.imei, self.partition["internalId"])
            self._attr_alarm_state = target_state
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Failed to set alarm (%s): %s", mode, ex)
            self._attr_alarm_state = previous_state
            self.async_write_ha_state()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._async_set_alarm(
            ALARM_MODES["DISARM"],
            AlarmControlPanelState.DISARMED,
            AlarmControlPanelState.DISARMING
        )

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._async_set_alarm(
            ALARM_MODES["ARM_AWAY"],
            AlarmControlPanelState.ARMED_AWAY,
            AlarmControlPanelState.ARMING
        )

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._async_set_alarm(
            ALARM_MODES["ARM_HOME"],
            AlarmControlPanelState.ARMED_HOME,
            AlarmControlPanelState.ARMING
        )
