"""Adds config flow for Eldes Alarms."""
import logging
import asyncio
import aiohttp
import voluptuous as vol
from http import HTTPStatus

from homeassistant import config_entries, core, exceptions
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .core.eldes_cloud import EldesCloud
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str
    }
)


class EldesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eldes."""

    VERSION = 1

    def __init__(self):
        """Start the eldes config flow."""
        self._reauth_entry = None
        self._username = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            unique_id = user_input[CONF_USERNAME].lower()
            await self.async_set_unique_id(unique_id)

            session = async_get_clientsession(self.hass)
            eldes_client = EldesCloud(session, self._username, self._password)

            try:
                await eldes_client.login()
            except (asyncio.TimeoutError, aiohttp.ClientError) as err:
                if err.status == HTTPStatus.UNAUTHORIZED:
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if not self._reauth_entry:
                    return self.async_create_entry(
                        title=user_input[CONF_USERNAME], data=user_input
                    )
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry, data=user_input, unique_id=unique_id
                )
                # Reload the config entry otherwise devices will remain unavailable
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                )
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
