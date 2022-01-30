"""Interfaces with Eldes control panels."""
import logging

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME
)
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_DISARMING,
    STATE_ALARM_ARMING
)

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

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_HOME

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        current_state = self.data["state"]

        self.data["state"] = STATE_ALARM_DISARMING
        self.async_write_ha_state()

        try:
            await self.client.set_alarm(
                ALARM_MODES["DISARM"],
                self.imei,
                self.entity_index
            )

            self.data["state"] = STATE_ALARM_DISARMED
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Failed to change state: %s", ex)
            self.data["state"] = current_state
            self.async_write_ha_state()

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        current_state = self.data["state"]

        self.data["state"] = STATE_ALARM_ARMING
        self.async_write_ha_state()

        try:
            await self.client.set_alarm(
                ALARM_MODES["ARM_AWAY"],
                self.imei,
                self.entity_index
            )

            self.data["state"] = STATE_ALARM_ARMED_AWAY
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Failed to change state: %s", ex)
            self.data["state"] = current_state
            self.async_write_ha_state()

    async def async_alarm_arm_home(self, code=None):
        """Send arm night command."""
        current_state = self.data["state"]

        self.data["state"] = STATE_ALARM_ARMING
        self.async_write_ha_state()

        try:
            await self.client.set_alarm(
                ALARM_MODES["ARM_HOME"],
                self.imei,
                self.entity_index
            )

            self.data["state"] = STATE_ALARM_ARMED_HOME
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Failed to change state: %s", ex)
            self.data["state"] = current_state
            self.async_write_ha_state()
