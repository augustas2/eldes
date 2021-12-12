"""Implementation for Eldes Cloud"""
import logging
import datetime
from aiohttp import ClientSession

from ..const import API_URL, API_PATHS

_LOGGER = logging.getLogger(__name__)


class EldesCloud:
    """Interacts with Eldes Alarm via public API."""
    timeout = 10

    def __init__(self, session: ClientSession):
        """Performs login and save session cookie."""
        # HTTPS Interface
        self.headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'x-whitelable': 'eldes'
        }
        self.refresh_token = ''
        self.refresh_at = datetime.datetime.now() + datetime.timedelta(minutes=3)

        self._http_session = session

    def _setOAuthHeader(self, data):
        # expires_in = float(data['expires_in'])
        expires_in = 120  # 2 minutes in seconds

        if 'refreshToken' in data:
            self.refresh_token = data['refreshToken']

        if expires_in is not None:
            self.refresh_at = datetime.datetime.now()
            self.refresh_at = self.refresh_at + datetime.timedelta(seconds=expires_in)

            # we substract 30 seconds from the correct refresh time
            # then we have a 30 seconds timespan to get a new refresh_token
            self.refresh_at = self.refresh_at + datetime.timedelta(seconds=-30)

        if 'token' in data:
            self.headers['Authorization'] = 'Bearer ' + data['token']

    async def _api_call(self, url, method, data=None):
        response = await self._http_session.request(
            method,
            url,
            timeout=self.timeout,
            json=data,
            headers=self.headers
        )

        return response

    async def login(self, username, password):
        data = {
            'email': username,
            'password': password,
            'hostDeviceId': ''
        }

        url = f"{API_URL}{API_PATHS['AUTH']}login"

        response = await self._api_call(url, "POST", data)
        result = await response.json()

        _LOGGER.debug(
            "login result: %s",
            result
        )

        self._setOAuthHeader(result)

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

        self._setOAuthHeader(result)

        return result

    async def get_devices(self):
        """Gets device list."""
        url = f"{API_URL}{API_PATHS['DEVICE']}list"

        response = await self._api_call(url, "GET")
        result = await response.json()

        _LOGGER.debug(
            "get_devices result: %s",
            result
        )

        return result

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

        _LOGGER.debug(
            "get_device_partitions result: %s",
            result
        )

        return result

    async def get_device_outputs(self, imei):
        """Gets device outputs/automations."""
        data = {
            'imei': imei
        }

        url = f"{API_URL}{API_PATHS['DEVICE']}list-outputs/{imei}"

        response = await self._api_call(url, "POST", data)
        result = await response.json()

        _LOGGER.debug(
            "get_device_outputs result: %s",
            result
        )

        return result

    async def set_alarm(self, mode, imei, zone_id):
        """Sets alarm to given mode."""
        data = {
            'imei': imei,
            'partitionIndex': zone_id
        }

        url = f"{API_URL}{API_PATHS['DEVICE']}action/{mode}"

        response = await self._api_call(url, "POST", data)

        _LOGGER.debug(
            "set_alarm response: %s",
            response
        )

        return response

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
        """Turns on output."""
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
