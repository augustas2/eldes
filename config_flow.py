"""Adds config flow for Eldes Alarms."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .const import DOMAIN
from .core.eldes_cloud import EldesCloud

_LOGGER = logging.getLogger(__name__)

class EldesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Eldes Alarms."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        data_schema = {
            vol.Required("email"): str,
            vol.Required("password"): str,
        }

        if user_input is not None:
            session = async_create_clientsession(self.hass)
            cloud = EldesCloud(session)
            await cloud.login(user_input['email'], user_input['password'])

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors
        )
