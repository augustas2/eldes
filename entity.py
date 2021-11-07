"""Base class for Eldes entity."""
from homeassistant.helpers.entity import Entity

from .const import DEFAULT_NAME, DEFAULT_ZONE, DOMAIN


class EldesDeviceEntity(Entity):
    """Base implementation for Eldes device."""

    def __init__(self, device_info):
        """Initialize a Tado device."""
        super().__init__()
        self._device_info = device_info
        self.device_name = device_info["info"]["model"]
        self.device_id = device_info["imei"]

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.device_name,
            "manufacturer": DEFAULT_NAME,
            "sw_version": self._device_info["info"]["firmware"],
            "model": self._device_info["info"]["model"]
        }

    @property
    def should_poll(self):
        """Do not poll."""
        return False


class EldesZoneEntity(Entity):
    """Base implementation for Eldes zone/partition."""

    def __init__(self, device_imei, zone_name, home_id, zone_id):
        """Initialize a Eldes zone."""
        super().__init__()
        self._device_zone_id = f"{home_id}_{zone_id}"
        self.zone_name = zone_name
        self.zone_id = zone_id
        self.device_id = device_imei

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return {
            "identifiers": {(DOMAIN, self._device_zone_id)},
            "name": self.zone_name,
            "manufacturer": DEFAULT_NAME,
            "model": DEFAULT_ZONE,
            "suggested_area": self.zone_name,
        }

    @property
    def should_poll(self):
        """Do not poll."""
        return False
