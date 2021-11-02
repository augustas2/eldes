"""
Implementation for Eldes Cloud
"""

import logging
import datetime
from requests import Session

from ..const import API_URL, API_PATHS

_LOGGER = logging.getLogger(__name__)


class EldesCloud:
    """Interacts with a Eldes Alarm via public API."""

    timeout = 10

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

    def _login(self, username, password):
        data = {
            'email': username,
            'password': password,
            'hostDeviceId': ''
        }

        url = API_URL + "" + API_PATHS["AUTH"] + "login"

        response = self._http_session.request(
            "post",
            url,
            timeout=self.timeout,
            json=data,
            headers=self.headers
        ).json()

        self._setOAuthHeader(response)

    def renew_token(self):
        """Updates auth token."""
        headers = self.headers
        headers['Authorization'] = 'Bearer ' + self.refresh_token

        url = API_URL + "" + API_PATHS["AUTH"] + "token"

        response = self._http_session.request(
            "get",
            url,
            timeout=self.timeout,
            headers=headers
        ).json()

        _LOGGER.debug(
            "renew_token response: %s",
            response
        )

        self._setOAuthHeader(response)

    def get_devices(self):
        """Gets device list."""
        url = API_URL + "" + API_PATHS["DEVICE"] + "list"

        response = self._http_session.request(
            "get",
            url,
            headers=self.headers,
            timeout=self.timeout
        ).json()

        _LOGGER.debug(
            "get_devices response: %s",
            response
        )

        return response

    def get_device_info(self, imei):
        """Gets device information."""
        url = API_URL + "" + API_PATHS["DEVICE"] + "info?imei=" + imei

        response = self._http_session.request(
            "get",
            url,
            headers=self.headers,
            timeout=self.timeout
        ).json()

        _LOGGER.debug(
            "get_device_info response: %s",
            response
        )

        return response

    def get_device_partitions(self, imei):
        """Gets device partitions/zones."""
        data = {
            'imei': imei
        }

        url = API_URL + "" + API_PATHS["DEVICE"] + "partition/list?imei=" + imei

        response = self._http_session.request(
            "post",
            url,
            headers=self.headers,
            json=data,
            timeout=self.timeout
        ).json()

        _LOGGER.debug(
            "get_device_partitions response: %s",
            response
        )

        return response

    def set_alarm(self, mode, imei, zone_id):
        """Sets alarm to given mode."""
        data = {
            'imei': imei,
            'partitionIndex': zone_id
        }

        url = API_URL + "" + API_PATHS["DEVICE"] + "action/" + mode

        response = self._http_session.request(
            "post",
            url,
            headers=self.headers,
            json=data,
            timeout=self.timeout
        )

        _LOGGER.debug(
            "set_alarm response: %s",
            response
        )

        return response

    # Ctor
    def __init__(self, username, password, timeout=10, http_session=None):
        """Performs login and save session cookie."""
        # HTTPS Interface
        self.headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'x-whitelable': 'eldes'
        }
        self.refresh_token = ''
        self.refresh_at = datetime.datetime.now() + datetime.timedelta(minutes=3)

        self._http_session = http_session if http_session else Session()
        self._login(username, password)
