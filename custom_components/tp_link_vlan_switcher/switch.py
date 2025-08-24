import logging
import requests
from homeassistant.components.switch import SwitchEntity
from .const import (
    DOMAIN,
    CONF_IP,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_VLANS,
    CONF_VID,
    CONF_VNAME,
    CONF_SELTYPE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up VLAN switches from a config entry."""
    ip = entry.data[CONF_IP]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    vlans = entry.options.get(CONF_VLANS, [])

    entities = []
    for vlan in vlans:
        entities.append(VlanSwitch(ip, username, password, vlan))
    async_add_entities(entities, update_before_add=False)


class VlanSwitch(SwitchEntity):
    """Representation of a VLAN switch."""

    def __init__(self, ip, username, password, vlan):
        self._ip = ip
        self._username = username
        self._password = password
        self._vlan = vlan
        self._attr_name = f"VLAN {vlan[CONF_VID]} {vlan[CONF_VNAME]}"
        self._state = False

    @property
    def is_on(self):
        return self._state

    def turn_on(self, **kwargs):
        self._apply_config(enabled=True)
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        self._apply_config(enabled=False)
        self._state = False
        self.schedule_update_ha_state()

    def _apply_config(self, enabled: bool):
        """Login and apply VLAN config via HTTP."""
        session = requests.Session()
        try:
            # Login
            login_url = f"http://{self._ip}/logon.cgi"
            session.post(
                login_url,
                data={
                    "username": self._username,
                    "password": self._password,
                    "cpassword": "",
                    "logon": "Login",
                },
                timeout=5,
            )

            # Build VLAN params
            params = {
                "vid": self._vlan[CONF_VID],
                "vname": self._vlan[CONF_VNAME],
            }
            for port, mapping in self._vlan[CONF_SELTYPE].items():
                params[f"selType_{port}"] = (
                    mapping["enabled"] if enabled else mapping["disabled"]
                )

            params["qvlan_add"] = "Add/Modify"

            url = f"http://{self._ip}/qvlanSet.cgi"
            r = session.get(url, params=params, timeout=5)
            r.raise_for_status()

            # Example: fetch HTML and parse status (optional, disabled now)
            # status_url = f"http://{self._ip}/some_status_page.cgi"
            # html = session.get(status_url).text
            # TODO: parse HTML table and update self._state

        except Exception as e:
            _LOGGER.error("Failed to apply VLAN config for %s: %s", self._vlan, e)
        finally:
            session.close()
