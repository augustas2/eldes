"""Adds config flow for Eldes Alarms."""
import logging
import requests.exceptions
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .core.eldes_cloud import EldesCloud
from .const import DOMAIN, UNIQUE_ID

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str
    }
)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    try:
        eldes = await hass.async_add_executor_job(
            EldesCloud, data[CONF_USERNAME], data[CONF_PASSWORD]
        )
        devices = await hass.async_add_executor_job(eldes.get_devices)
    except KeyError as ex:
        raise InvalidAuth from ex
    except RuntimeError as ex:
        raise CannotConnect from ex
    except requests.exceptions.HTTPError as ex:
        if ex.response.status_code > 400 and ex.response.status_code < 500:
            raise InvalidAuth from ex
        raise CannotConnect from ex

    if "deviceListEntries" not in devices or len(devices["deviceListEntries"]) == 0:
        raise NoHomes

    home = devices["deviceListEntries"][0]
    unique_id = str(home["imei"])
    name = home["name"]

    return {"title": name, UNIQUE_ID: unique_id}


class EldesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Eldes Alarms."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                validated = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except NoHomes:
                errors["base"] = "no_homes"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if "base" not in errors:
                await self.async_set_unique_id(validated[UNIQUE_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=validated["title"], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class NoHomes(exceptions.HomeAssistantError):
    """Error to indicate the account has no homes."""
