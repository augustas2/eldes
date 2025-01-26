"""Implementation for Eldes Cloud"""
import asyncio
import async_timeout
import logging
import aiohttp

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelState
)

from ..const import API_URL, API_PATHS

_LOGGER = logging.getLogger(__name__)

ALARM_STATES_MAP = {
    "DISARMED": AlarmControlPanelState.DISARMED,
    "ARMED": AlarmControlPanelState.ARMED_AWAY,
    "ARMSTAY": AlarmControlPanelState.ARMED_HOME
}


class EldesCloud:
    """Interacts with Eldes via public API."""

    def __init__(self, session: aiohttp.ClientSession, username: str, password: str):
        """Performs login and save session cookie."""
        self.timeout = 30
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

    async def _call(self, url, method, data=None):
        async with async_timeout.timeout(self.timeout):
            return await self._http_session.request(
                method,
                url,
                json=data,
                headers=self.headers
            )

    async def _api_call(self, url, method, data=None):
        try:
            req = await self._call(url, method, data)

            if req.status == 401:
                await self.login()
                req = await self._call(url, method, data)
            elif req.status == 403:
                await self.renew_token()
                req = await self._call(url, method, data)

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

        resp = await self._call(url, "POST", data)
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

        if response.status == 401:
            return await self.login()

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
            partitions[partitionIndex]["state"] = ALARM_STATES_MAP[partitions[partitionIndex].get("state", AlarmControlPanelState.DISARMED)]

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

    async def get_temperatures(self, imei):
        """Gets device information."""
        url = f"{API_URL}{API_PATHS['DEVICE']}temperatures?imei={imei}"

        response = await self._api_call(url, "POST", {})
        result = await response.json()
        temperatures = result.get("temperatureDetailsList", [])

        _LOGGER.debug(
            "get_temperatures result: %s",
            temperatures
        )

        return temperatures

    async def get_events(self, size):
        """Gets device events."""
        data = {
            "": "",
            "size": size,
            "start": 0
        }

        url = f"{API_URL}{API_PATHS['DEVICE']}event/list"

        response = await self._api_call(url, "POST", data)
        result = await response.json()
        events = result.get("eventDetails", [])

        _LOGGER.debug(
            "get_events result: %s",
            events
        )

        return events
