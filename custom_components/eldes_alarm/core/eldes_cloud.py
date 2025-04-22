"""Implementation for Eldes Cloud"""
import asyncio
import async_timeout
import logging
import aiohttp
from datetime import datetime, timedelta

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
        self.timeout = 30
        self.headers = {
            "X-Requested-With": "XMLHttpRequest",
            "x-whitelable": "eldes"
        }
        self.refresh_token = ""
        self.token_expires_at = None

        self._http_session = session
        self._username = username
        self._password = password

    async def _setOAuthHeader(self, data):
        if "refreshToken" in data:
            self.refresh_token = data["refreshToken"]

        if "token" in data:
            self.headers["Authorization"] = f"Bearer {data['token']}"
            self.token_expires_at = datetime.utcnow() + timedelta(minutes=4)  # token lasts 5 minutes, refresh 1 minute before

        return data

    async def _api_call(self, url, method, data=None):
        try:
            _LOGGER.debug("API Call -> %s %s | Headers: %s | Data: %s", method, url, self.headers, data)

            async with async_timeout.timeout(self.timeout):
                req = await self._http_session.request(
                    method,
                    url,
                    json=data,
                    headers=self.headers
                )

            req.raise_for_status()
            return req

        except aiohttp.ClientResponseError as err:
            _LOGGER.error("Client response error on API %s request: %s", url, err)
            raise

        except aiohttp.ClientError as err:
            _LOGGER.error("Client error on API %s request: %s", url, err)
            raise

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout error on API request: %s", url)
            raise

    async def _safe_api_call(self, url, method, data=None):
        try:
            return await self._api_call(url, method, data)

        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                _LOGGER.warning("Auth error (%s) on %s - attempting to re-authenticate.", err.status, url)
                await self.login()
                try:
                    return await self._api_call(url, method, data)
                except Exception as retry_err:
                    _LOGGER.error("Retry failed for %s: %s", url, retry_err)
                    raise
            raise

    async def login(self):
        data = {
            "email": self._username,
            "password": self._password,
            "hostDeviceId": ""
        }

        url = f"{API_URL}{API_PATHS['AUTH']}login"
        resp = await self._api_call(url, "POST", data)
        result = await resp.json()

        _LOGGER.debug("login result: %s", result)
        return await self._setOAuthHeader(result)

    async def renew_token(self):
        if not self.token_expires_at or datetime.utcnow() < self.token_expires_at:
            _LOGGER.debug("Token is still valid; skipping token refresh.")
            return

        self.headers["Authorization"] = f"Bearer {self.refresh_token}"
        url = f"{API_URL}{API_PATHS['AUTH']}token"

        try:
            async with async_timeout.timeout(self.timeout):
                response = await self._http_session.get(url, headers=self.headers)

            response.raise_for_status()
            result = await response.json()

            _LOGGER.debug("Token successfully refreshed: %s", result)
            return await self._setOAuthHeader(result)

        except aiohttp.ClientResponseError as err:
            _LOGGER.error("Token refresh failed: %s", err)
            raise

        except Exception as e:
            _LOGGER.error("Unexpected error during token refresh: %s", e)
            raise

    async def get_devices(self):
        url = f"{API_URL}{API_PATHS['DEVICE']}list"
        response = await self._safe_api_call(url, "GET")
        result = await response.json()
        return result.get("deviceListEntries", [])

    async def get_device_info(self, imei):
        url = f"{API_URL}{API_PATHS['DEVICE']}info?imei={imei}"
        response = await self._safe_api_call(url, "GET")
        return await response.json()

    async def get_device_partitions(self, imei):
        data = {"imei": imei}
        url = f"{API_URL}{API_PATHS['DEVICE']}partition/list?imei={imei}"
        response = await self._safe_api_call(url, "POST", data)
        result = await response.json()
        partitions = result.get("partitions", [])

        for partition in partitions:
            state = partition.get("state", AlarmControlPanelState.DISARMED)
            partition["state"] = ALARM_STATES_MAP.get(state, AlarmControlPanelState.DISARMED)

        return partitions

    async def get_device_outputs(self, imei):
        data = {"imei": imei}
        url = f"{API_URL}{API_PATHS['DEVICE']}list-outputs/{imei}"
        response = await self._safe_api_call(url, "POST", data)
        result = await response.json()
        return result.get("deviceOutputs", [])

    async def set_alarm(self, mode, imei, zone_id):
        data = {"imei": imei, "partitionIndex": zone_id}
        url = f"{API_URL}{API_PATHS['DEVICE']}action/{mode}"
        response = await self._safe_api_call(url, "POST", data)
        return await response.text()

    async def turn_on_output(self, imei, output_id):
        url = f"{API_URL}{API_PATHS['DEVICE']}control/enable/{imei}/{output_id}"
        response = await self._safe_api_call(url, "PUT", {})
        return response

    async def turn_off_output(self, imei, output_id):
        url = f"{API_URL}{API_PATHS['DEVICE']}control/disable/{imei}/{output_id}"
        response = await self._safe_api_call(url, "PUT", {})
        return response

    async def get_temperatures(self, imei):
        url = f"{API_URL}{API_PATHS['DEVICE']}temperatures?imei={imei}"
        response = await self._safe_api_call(url, "POST", {})
        result = await response.json()
        return result.get("temperatureDetailsList", [])

    async def get_events(self, size):
        data = {"": "", "size": size, "start": 0}
        url = f"{API_URL}{API_PATHS['DEVICE']}event/list"
        response = await self._safe_api_call(url, "POST", data)
        result = await response.json()
        return result.get("eventDetails", [])
