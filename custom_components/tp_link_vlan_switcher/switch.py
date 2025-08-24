import logging
import requests
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from .const import (
    DOMAIN,
    CONF_IP,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_VLANS,
    CONF_VID,
    CONF_VNAME,
    CONF_VLAN,
    CONF_PVID,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up VLAN switches from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]

    ip = data[CONF_IP]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    vlans = data[CONF_VLANS]

    switches = [
        VlanSwitch(ip, username, password, vlan_conf) for vlan_conf in vlans
    ]
    async_add_entities(switches, True)


class VlanSwitch(SwitchEntity):
    """Representation of a VLAN configuration switch."""

    def __init__(self, ip: str, username: str, password: str, vlan_conf: dict):
        self._ip = ip
        self._username = username
        self._password = password
        self._vlan = vlan_conf
        self._attr_name = f"VLAN {vlan_conf[CONF_VID]} {vlan_conf[CONF_VNAME]}"
        self._attr_unique_id = f"{DOMAIN}_{ip}_{vlan_conf[CONF_VID]}"
        self._attr_is_on = False
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    def turn_on(self, **kwargs):
        self._apply_config(enabled=True)
        self._attr_is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        self._apply_config(enabled=False)
        self._attr_is_on = False
        self.schedule_update_ha_state()

    def _apply_config(self, enabled: bool):
        """Apply VLAN and PVID configuration via HTTP requests."""
        try:
            session = requests.Session()

            # 1. Login
            login_url = f"http://{self._ip}/logon.cgi"
            login_data = {
                "username": self._username,
                "password": self._password,
                "cpassword": "",
                "logon": "Login",
            }
            _LOGGER.debug("Logging in to %s", login_url)
            session.post(login_url, data=login_data, timeout=5)

            # 2. VLAN Config
            vlan_params = {
                "vid": self._vlan[CONF_VID],
                "vname": self._vlan[CONF_VNAME],
                "qvlan_add": "Add/Modify",
            }
            vlan_config = self._vlan[CONF_VLAN]["turn_on" if enabled else "turn_off"]
            for port, value in vlan_config.items():
                vlan_params[f"selType_{port}"] = value

            vlan_url = f"http://{self._ip}/qvlanSet.cgi"
            _LOGGER.debug("Sending VLAN config to %s with %s", vlan_url, vlan_params)
            session.get(vlan_url, params=vlan_params, timeout=5)

            # 3. PVID Config
            pvid_config = self._vlan[CONF_PVID]["turn_on" if enabled else "turn_off"]
            for pvid, ports in pvid_config.items():
                pbm = sum(1 << (p - 1) for p in ports)  # Bitmask
                pvid_url = f"http://{self._ip}/vlanPvidSet.cgi"
                params = {"pbm": pbm, "pvid": pvid}
                _LOGGER.debug("Sending PVID config to %s with %s", pvid_url, params)
                session.get(pvid_url, params=params, timeout=5)

            # 4. Logout
            logout_url = f"http://{self._ip}/Logout.htm"
            _LOGGER.debug("Logging out from %s", logout_url)
            session.get(logout_url, timeout=5)

        except Exception as e:
            _LOGGER.error("Error applying VLAN config: %s", e)
