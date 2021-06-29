import logging

from aiohttp import ClientSession

from ..const import API_URL, API_PATHS

_LOGGER = logging.getLogger(__name__)


class EldesCloud:
    auth = None
    devices = None

    def __init__(self, session: ClientSession):
        self.session = session

    async def login(self, email: str, password: str):
        try:
            data = {
                'email': email,
                'password': password,
                'hostDeviceId': ''
            }

            r = await self.session.post(
                API_URL + "" + API_PATHS["AUTH"],
                json=data,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "x-whitelable": "eldes"
                })
            auth = await r.json()
            self.auth = auth
            _LOGGER.info(auth)

            devices = await self.get_devices()
            if devices is None:
                return False

            for index, device in enumerate(devices):
                device_info = await self.get_device_info(device["imei"])
                if device_info is None:
                    return False
                devices[index]["info"] = device_info

            self.devices = devices
            _LOGGER.info(devices)

            return True

        except Exception as e:
            _LOGGER.exception(f"Can't login to Eldes Cloud Services: {e}")
            return False

    async def get_devices(self):
        try:
            r = await self.session.get(
                API_URL + "" + API_PATHS["DEVICE"] + "list",
                headers={
                    "Authorization": "Bearer " + self.auth["token"]
                }
            )
            resp = await r.json()
            return resp["deviceListEntries"]
        except Exception as e:
            _LOGGER.exception(f"Can't retrieve device list: {e}")

        return None

    async def get_device_info(self, device_imei: str):
        try:
            r = await self.session.get(
                API_URL + "" + API_PATHS["DEVICE"] + "info?imei=" + device_imei,
                headers={
                    "Authorization": "Bearer " + self.auth["token"]
                }
            )
            resp = await r.json()
            return resp
        except Exception as e:
            _LOGGER.exception(f"Can't retrieve device info: {e}")

        return None
