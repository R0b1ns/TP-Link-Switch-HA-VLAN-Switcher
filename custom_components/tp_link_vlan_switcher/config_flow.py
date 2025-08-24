import re
import logging
import requests
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, CONF_IP, CONF_USERNAME, CONF_PASSWORD

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

            ok, reason = await self.hass.async_add_executor_job(
                self._test_login, ip, username, password
            )
            if ok:
                return self.async_create_entry(
                    title=f"VLAN Switch {ip}", data=user_input
                )

            # Map reason -> HA error key
            if reason == "invalid_auth":
                errors["base"] = "invalid_auth"
            elif reason == "cannot_connect":
                errors["base"] = "cannot_connect"
            else:
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required(CONF_IP, description={"name": "IP-Adresse"}): str,
            vol.Required(CONF_USERNAME, description={"name": "Benutzername"}): str,
            vol.Required(CONF_PASSWORD, description={"name": "Passwort"}): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    def _test_login(self, ip: str, username: str, password: str):
        """Do a blocking login test and parse TP-Link logonInfo array."""
        try:
            with requests.Session() as s:
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
                    return False, "cannot_connect"

                # Parse errType from embedded JS
                m = LOGIN_PATTERN.search(resp.text)
                if not m:
                    _LOGGER.debug("logonInfo array not found in response")
                    return False, "cannot_connect"

                err_type = int(m.group(1))
                _LOGGER.debug("Parsed errType=%s from login page", err_type)

                if err_type == 0:
                    # optional: gleich wieder ausloggen
                    try:
                        s.get(f"http://{ip}/Logout.htm", timeout=5)
                    except Exception:
                        pass
                    return True, ""

                if err_type in ERR_INVALID_AUTH:
                    return False, "invalid_auth"

                if err_type in ERR_CANNOT_CONNECT:
                    return False, "cannot_connect"

                return False, "unknown"

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Login test request error: %s", e)
            return False, "cannot_connect"
        except Exception as e:
            _LOGGER.exception("Unexpected error during login test: %s", e)
            return False, "unknown"

    @staticmethod
    def async_get_options_flow(config_entry):
        """Bind options flow."""
        from .options_flow import VlanSwitchOptionsFlowHandler
        return VlanSwitchOptionsFlowHandler(config_entry)
