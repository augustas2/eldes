"""Implementation for Eldes Cloud"""
import asyncio
import async_timeout
import logging
import datetime
import aiohttp
from http import HTTPStatus
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED
)

from ..const import API_URL, API_PATHS

_LOGGER = logging.getLogger(__name__)

ALARM_STATES_MAP = {
    "DISARMED": STATE_ALARM_DISARMED,
    "ARMED": STATE_ALARM_ARMED_AWAY,
    "ARMSTAY": STATE_ALARM_ARMED_HOME
}


class EldesCloud:
    """Interacts with Eldes via public API."""

    def __init__(self, session: aiohttp.ClientSession, username: str, password: str):
        """Performs login and save session cookie."""
        self.timeout = 10
        self.headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'x-whitelable': 'eldes'
        }
        self.refresh_token = ''

        self._http_session = session
        self._username = username
        self._password = password

    async def _setOAuthHeader(self, data):
        if 'refreshToken' in data:
            self.refresh_token = data['refreshToken']

        if 'token' in data:
            self.headers['Authorization'] = f"Bearer {data['token']}"

        return data

    async def _api_call(self, url, method, data=None):
        try:
            async with async_timeout.timeout(self.timeout):
                req = await self._http_session.request(
                    method,
                    url,
                    json=data,
                    headers=self.headers
                )
            req.raise_for_status()
            return req

        except aiohttp.ClientError as err:
            _LOGGER.error("Client error on API %s request %s", url, err)
            raise

        except asyncio.TimeoutError:
            _LOGGER.error("Client timeout error on API request %s", url)
            raise

    async def login(self):
        data = {
            'email': self._username,
            'password': self._password,
            'hostDeviceId': ''
        }

        url = f"{API_URL}{API_PATHS['AUTH']}login"

        resp = await self._api_call(url, "POST", data)
        result = await resp.json()

        _LOGGER.debug(
            "login result: %s",
            result
        )

        return await self._setOAuthHeader(result)

    async def renew_token(self):
        """Updates auth token."""
        headers = self.headers
        headers['Authorization'] = f"Bearer {self.refresh_token}"

        url = f"{API_URL}{API_PATHS['AUTH']}token"

        response = await self._http_session.get(
            url,
            timeout=self.timeout,
            headers=headers
        )
        result = await response.json()

        _LOGGER.debug(
            "renew_token result: %s",
            result
        )

        return await self._setOAuthHeader(result)

    async def get_devices(self):
        """Gets device list."""
        url = f"{API_URL}{API_PATHS['DEVICE']}list"

        response = await self._api_call(url, "GET")
        result = await response.json()
        devices = result.get("deviceListEntries", [])

        _LOGGER.debug(
            "get_devices result: %s",
            devices
        )

        return devices

    async def get_device_info(self, imei):
        """Gets device information."""
        url = f"{API_URL}{API_PATHS['DEVICE']}info?imei={imei}"

        response = await self._api_call(url, "GET")
        result = await response.json()

        _LOGGER.debug(
            "get_device_info result: %s",
            result
        )

        return result

    async def get_device_partitions(self, imei):
        """Gets device partitions/zones."""
        data = {
            'imei': imei
        }

        url = f"{API_URL}{API_PATHS['DEVICE']}partition/list?imei={imei}"

        response = await self._api_call(url, "POST", data)
        result = await response.json()
        partitions = result.get("partitions", [])

        # Replace Eldes state with HA state name
        for partitionIndex, _ in enumerate(partitions):
            partitions[partitionIndex]["state"] = ALARM_STATES_MAP[partitions[partitionIndex].get("state", STATE_ALARM_DISARMED)]

        _LOGGER.debug(
            "get_device_partitions result: %s",
            partitions
        )

        return partitions

    async def get_device_outputs(self, imei):
        """Gets device outputs/automations."""
        data = {
            'imei': imei
        }

        url = f"{API_URL}{API_PATHS['DEVICE']}list-outputs/{imei}"

        response = await self._api_call(url, "POST", data)
        result = await response.json()
        outputs = result.get("deviceOutputs", [])

        _LOGGER.debug(
            "get_device_outputs result: %s",
            outputs
        )

        return outputs

    async def set_alarm(self, mode, imei, zone_id):
        """Sets alarm to provided mode."""
        data = {
            'imei': imei,
            'partitionIndex': zone_id
        }

        url = f"{API_URL}{API_PATHS['DEVICE']}action/{mode}"

        response = await self._api_call(url, "POST", data)
        result = await response.text()

        _LOGGER.debug(
            "set_alarm result: %s",
            result
        )

        return result

    async def turn_on_output(self, imei, output_id):
        """Turns on output."""
        data = {
            "": ""
        }

        url = f"{API_URL}{API_PATHS['DEVICE']}control/enable/{imei}/{output_id}"

        response = await self._api_call(url, "PUT", data)

        _LOGGER.debug(
            "turn_on_output response: %s",
            response
        )

        return response

    async def turn_off_output(self, imei, output_id):
        """Turns off output."""
        data = {
            "": ""
        }

        url = f"{API_URL}{API_PATHS['DEVICE']}control/disable/{imei}/{output_id}"

        response = await self._api_call(url, "PUT", data)

        _LOGGER.debug(
            "turn_off_output response: %s",
            response
        )

        return response
