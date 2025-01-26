"""Interfaces with Eldes control panels."""
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    ALARM_MODES
)
from . import EldesZoneEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Eldes sensor platform."""
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = []

    for deviceIndex, _ in enumerate(coordinator.data):
        for partitionIndex, _ in enumerate(coordinator.data[deviceIndex]["partitions"]):
            entities.append(EldesAlarmPanel(client, coordinator, deviceIndex, partitionIndex))

    async_add_entities(entities)


class EldesAlarmPanel(EldesZoneEntity, AlarmControlPanelEntity):
    """Representation of an Eldes Alarm."""

    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_HOME
    )
    _attr_code_arm_required = False

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self.imei}_zone_{self.data['internalId']}"

    @property
    def name(self):
        """Return the name of the zone."""
        return self.data["name"]

    @property
    def state(self):
        """Return the state of the alarm."""
        return self.data["state"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "armed": self.data["armed"],
            "armStay": self.data["armStay"],
            "state": self.data["state"],
            "hasUnacceptedPartitionAlarms": self.data["hasUnacceptedPartitionAlarms"]
        }

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        current_state = self.data["state"]

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

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        current_state = self.data["state"]

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

    async def async_alarm_arm_home(self, code=None):
        """Send arm night command."""
        current_state = self.data["state"]

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
