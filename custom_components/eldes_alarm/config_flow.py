"""Adds config flow for Eldes."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_PIN, CONF_SCAN_INTERVAL

from .core.eldes_cloud import EldesCloud
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_EVENTS_LIST_SIZE,
    CONF_EVENTS_LIST_SIZE,
    CONF_DEVICE_IMEI,
    SCAN_INTERVAL_MIN,
    SCAN_INTERVAL_MAX,
    EVENTS_LIST_SIZE_MIN,
    EVENTS_LIST_SIZE_MAX,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_PIN): str
    }
)


class EldesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eldes."""
    VERSION = 1

    def __init__(self):
        self.client = None
        self.devices = []
        self.data = {}

    async def async_step_user(self, user_input=None):
        """Step 1: collect email and password."""
        errors = {}

        if user_input is not None:
            email = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            pin = user_input[CONF_PIN]

            try:
                session = async_get_clientsession(self.hass)
                self.client = EldesCloud(session, email, password, pin)
                await self.client.login()

                self.devices = await self.client.get_devices()
                if not self.devices:
                    errors["base"] = "no_devices"
                else:
                    self.data[CONF_USERNAME] = email
                    self.data[CONF_PASSWORD] = password
                    self.data[CONF_PIN] = pin
                    return await self.async_step_select_device()

            except Exception as ex:
                _LOGGER.error("Eldes login failed: %s", ex)
                errors["base"] = "auth_failed"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors
        )

    async def async_step_select_device(self, user_input=None):
        """Step 2: let user select device."""
        errors = {}

        device_options = {
            device["imei"]: f"{device['name']} ({device['imei']})"
            for device in self.devices
        }

        if user_input is not None:
            selected_imei = user_input["device"]
            selected_device = next((d for d in self.devices if d["imei"] == selected_imei), None)

            if selected_device:
                await self.async_set_unique_id(selected_imei)
                self._abort_if_unique_id_configured()

                self.data[CONF_DEVICE_IMEI] = selected_imei

                return self.async_create_entry(
                    title=selected_device["name"],
                    data=self.data
                )
            else:
                errors["base"] = "device_not_found"

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema({
                vol.Required("device"): vol.In(device_options)
            }),
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow for Eldes."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            # Extract PIN from user input
            new_pin = user_input.pop(CONF_PIN)

            # Update the main config data with new PIN
            new_data = dict(self._config_entry.data)
            new_data[CONF_PIN] = new_pin

            # Update both data and options
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data=new_data,
                options=user_input
            )

            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self._config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ): vol.All(
                        int,
                        vol.Range(min=SCAN_INTERVAL_MIN, max=SCAN_INTERVAL_MAX)
                    ),
                    vol.Required(
                        CONF_EVENTS_LIST_SIZE,
                        default=self._config_entry.options.get(CONF_EVENTS_LIST_SIZE, DEFAULT_EVENTS_LIST_SIZE)
                    ): vol.All(
                        int,
                        vol.Range(min=EVENTS_LIST_SIZE_MIN, max=EVENTS_LIST_SIZE_MAX)
                    ),
                    vol.Required(
                        CONF_PIN,
                        default=self._config_entry.data.get(CONF_PIN)
                    ): str,
                }
            )
        )
