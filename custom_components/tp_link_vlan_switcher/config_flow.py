import re
import logging
import requests
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, CONF_IP, CONF_USERNAME, CONF_PASSWORD, CONF_PORTS
from .utils import extract_js_object_field

_LOGGER = logging.getLogger(__name__)

LOGIN_PATTERN = re.compile(
    r"var\s+logonInfo\s*=\s*new\s+Array\s*\(\s*(\d+)\s*,", re.IGNORECASE
)

# Map TP-Link errType -> HA error bucket
ERR_INVALID_AUTH = {1, 2, 6}   # falsche Zugangsdaten
ERR_CANNOT_CONNECT = {3, 4, 5} # Session voll / nicht erreichbar


class VlanSwitchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for TP-Link VLAN Switcher."""

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            ip = user_input[CONF_IP].strip()
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]

            successful, error, device_info = await self.hass.async_add_executor_job(
                self._test_login, ip, username, password
            )
            if successful:
                return self.async_create_entry(
                    # TODO: merge user_input with device_info
                    title=device_info['descriStr'], data=user_input
                )

            # error is  -> HA error key
            errors["base"] = error

        data_schema = vol.Schema({
            vol.Required(CONF_IP, description={"name": "IP-Adresse"}): str,
            vol.Required(CONF_USERNAME, description={"name": "Benutzername"}): str,
            vol.Required(CONF_PASSWORD, description={"name": "Passwort"}): str,
            vol.Required(CONF_PORTS, description={"name": "Anzahl Ports"}, default=5): int,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    def _test_login(self, ip: str, username: str, password: str):
        """Do a blocking login test and parse TP-Link logonInfo array."""
        try:
            with requests.Session() as s:
                # 1. Login
                url = f"http://{ip}/logon.cgi"
                payload = {
                    "username": username,
                    "password": password,
                    "cpassword": "",
                    "logon": "Login",
                }
                resp = s.post(url, data=payload, timeout=8)
                if resp.status_code != 200:
                    _LOGGER.debug("Login HTTP status != 200: %s", resp.status_code)
                    return False, "cannot_connect", None

                # Parse errType from embedded JS
                m = LOGIN_PATTERN.search(resp.text)
                if not m:
                    _LOGGER.debug("logonInfo array not found in response")
                    return False, "cannot_connect", None

                err_type = int(m.group(1))
                _LOGGER.debug("Parsed errType=%s from login page", err_type)

                if err_type in ERR_INVALID_AUTH:
                    return False, "invalid_auth", None

                if err_type in ERR_CANNOT_CONNECT:
                    return False, "cannot_connect", None

                if err_type != 0:
                    return False, "unknown", None

                # 2. Get device info
                device_info = self._get_device_info(s, ip)

                # 3. Logout
                try:
                    s.get(f"http://{ip}/Logout.htm", timeout=5)
                except Exception:
                    pass

                if not device_info:
                    return False, "cannot_connect", None

                return True, None, device_info

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Login test request error: %s", e)
            return False, "cannot_connect"
        except Exception as e:
            _LOGGER.exception("Unexpected error during login test: %s", e)
            return False, "unknown"

    @staticmethod
    def _get_device_info(s, ip):
        try:
            resp_system_info = s.get(f"http://{ip}/SystemInfoRpm.htm")
        except Exception as e:
            _LOGGER.exception("Unexpected error during system info request: %s", e)
            return None

        if resp_system_info.status_code != 200:
            _LOGGER.warning("Unable to get device info, Status code: %s", resp_system_info.status_code)
            return None

        # Parse html
        return extract_js_object_field(resp_system_info.text, "info_ds")

    @staticmethod
    def async_get_options_flow(config_entry):
        """Bind options flow."""
        from .options_flow import VlanSwitchOptionsFlowHandler
        return VlanSwitchOptionsFlowHandler(config_entry)
