"""Interfaces with Eldes control panels."""
import logging

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
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
    DATA,
    DOMAIN,
    SIGNAL_ELDES_UPDATE_RECEIVED,
    ALARM_MODES
)
from .entity import EldesZoneEntity

_LOGGER = logging.getLogger(__name__)

ALARM_STATES_MAP = {
    "DISARMED": STATE_ALARM_DISARMED,
    "ARMED": STATE_ALARM_ARMED_AWAY,
    "ARMSTAY": STATE_ALARM_ARMED_HOME
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up a Eldes alarm control panel based on a config entry."""
    eldes = hass.data[DOMAIN][entry.entry_id][DATA]
    devices = eldes.devices
    entities = []

    # Create zone alarms
    try:
        for device in devices:
            entities.extend(
                [
                    EldesAlarmPanel(eldes, device, zone)
                    for zone in device["partitions"]
                ]
            )
    except KeyError:
        pass

    if entities:
        async_add_entities(entities, True)


class EldesAlarmPanel(EldesZoneEntity, AlarmControlPanelEntity):
    """Representation of an Eldes Alarm."""

    def __init__(self, eldes, device, zone):
        """Initialize of the Eldes Alarm."""
        super().__init__(device["imei"], zone["name"], eldes.home_id, zone["internalId"])
        self._eldes = eldes

        self._unique_id = f"{zone['internalId']} {eldes.home_id}"
        self._state_attributes = None
        self._state = None

    async def async_added_to_hass(self):
        """Register for zone updates."""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_ELDES_UPDATE_RECEIVED.format(
                    self._eldes.home_id, self.device_id
                ),
                self._async_update_callback,
            )
        )
        self._async_update_zone_data()

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the zone."""
        return self.zone_name

    @property
    def state(self):
        """Return the state of the alarm."""
        return self._state

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_HOME

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._state_attributes

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        self._state = STATE_ALARM_DISARMING
        self.async_write_ha_state()

        try:
            await self._eldes.eldes.set_alarm(
                ALARM_MODES["DISARM"],
                self.device_id,
                self.zone_id
            )
        except Exception as err:
            _LOGGER.error('Error while disarming "%s": %s', self.zone_name, err)
            return

        self._state = STATE_ALARM_DISARMED
        self.async_write_ha_state()

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        self._state = STATE_ALARM_ARMING
        self.async_write_ha_state()

        try:
            await self._eldes.eldes.set_alarm(
                ALARM_MODES["ARM_AWAY"],
                self.device_id,
                self.zone_id
            )
        except Exception as err:
            _LOGGER.error('Error while arming "%s" (away): %s', self.zone_name, err)
            return

        self._state = STATE_ALARM_ARMED_AWAY
        self.async_write_ha_state()

    async def async_alarm_arm_home(self, code=None):
        """Send arm night command."""
        self._state = STATE_ALARM_ARMING
        self.async_write_ha_state()

        try:
            await self._eldes.eldes.set_alarm(
                ALARM_MODES["ARM_HOME"],
                self.device_id,
                self.zone_id
            )
        except Exception as err:
            _LOGGER.error('Error while arming "%s" (home): %s', self.zone_name, err)
            return

        self._state = STATE_ALARM_ARMED_HOME
        self.async_write_ha_state()

    @callback
    def _async_update_callback(self):
        """Update and write state."""
        self._async_update_zone_data()
        self.async_write_ha_state()

    @callback
    def _async_update_zone_data(self):
        """Handle update callbacks."""
        try:
            zone_info = next(
                (
                    zone for zone in self._eldes.data[self.device_id]["partitions"]
                    if zone["internalId"] == self.zone_id
                ), None
            )

            if zone_info is not None:
                self._state = ALARM_STATES_MAP[zone_info.get("state", "DISARMED")]
                self._state_attributes = {
                    "armed": zone_info.get("armed", False),
                    "armStay": zone_info.get("armStay", False),
                    "hasUnacceptedPartitionAlarms": zone_info.get("hasUnacceptedPartitionAlarms", False),
                }
        except KeyError:
            pass
