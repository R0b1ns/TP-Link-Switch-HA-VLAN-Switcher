import logging
from typing import Any, Dict
import requests

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify

from .const import DOMAIN, CONF_IP, CONF_USERNAME, CONF_PASSWORD, CONF_VLANS, CONF_PVID

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    data = entry.data
    options = entry.options or {}

    switches: Dict[str, Dict[str, Any]] = options.get("switches", {})
    if not switches:
        _LOGGER.debug("[%s] Keine Switch-Profile in options -> keine Entitäten", entry.entry_id)
        return

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    current_entities = hass.data[DOMAIN][entry.entry_id]

    # Entferne Entitäten, die nicht mehr existieren
    to_remove = [name for name in current_entities if name not in switches]
    for name in to_remove:
        switch = current_entities.pop(name)
        await switch.async_remove()

    # Füge neue Entitäten hinzu
    new_entities = []
    for name, cfg in switches.items():
        if name not in current_entities:
            vlans = cfg.get(CONF_VLANS, {}) or {}
            pvid = cfg.get(CONF_PVID, {}) or {}
            switch = TpLinkVlanProfileSwitch(entry=entry, name=name, vlans=vlans, pvid=pvid)
            current_entities[name] = switch
            new_entities.append(switch)

    if new_entities:
        async_add_entities(new_entities)


class TpLinkVlanProfileSwitch(SwitchEntity):
    """Eine Switch-Entity, die beim Ein-/Ausschalten VLAN- & PVID-Profile anwendet."""

    def __init__(self, entry, name: str, vlans: dict, pvid: dict):
        self._entry = entry
        self._ip = entry.data.get(CONF_IP)
        self._user = entry.data.get(CONF_USERNAME)
        self._pwd = entry.data.get(CONF_PASSWORD)

        self._profile_name = name
        self._vlans = vlans
        self._pvid = pvid
        self._is_on = False

        self._attr_name = f"{name}"
        self._attr_unique_id = f"{entry.entry_id}_{slugify(name)}"

    @property
    def device_info(self) -> DeviceInfo:
        """Registriere ein Gerät, unter dem alle Profil-Switches dieser Config hängen."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            manufacturer="TP-Link",
            name=f"TP-Link VLAN Switch {self._ip}",
            model="VLAN Profile",
            configuration_url=f"http://{self._ip}/",
        )

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs):
        ok = await self.hass.async_add_executor_job(self._apply_profile, "turn_on")
        if ok:
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        ok = await self.hass.async_add_executor_job(self._apply_profile, "turn_off")
        if ok:
            self._is_on = False
            self.async_write_ha_state()

    def _apply_profile(self, phase: str) -> bool:
        """phase = 'turn_on' oder 'turn_off'."""
        try:
            s = requests.Session()
            # Login
            login = s.post(
                f"http://{self._ip}/logon.cgi",
                data={"username": self._user, "password": self._pwd, "cpassword": "", "logon": "Login"},
                timeout=8,
            )
            if login.status_code != 200:
                _LOGGER.error("Login fehlgeschlagen (%s): HTTP %s", self._ip, login.status_code)
                return False

            # VLAN anwenden
            vlan_cfg = self._vlans.get(phase, {})
            if vlan_cfg:
                _LOGGER.debug("Würde VLAN anwenden (%s): %s", phase, vlan_cfg)

            # PVID anwenden
            pvid_cfg = self._pvid.get(phase, {})
            if pvid_cfg:
                for pvid_str, ports in pvid_cfg.items():
                    pbm = 0
                    for p in ports:
                        if isinstance(p, int) and p >= 1:
                            pbm |= (1 << (p - 1))
                    url = f"http://{self._ip}/vlanPvidSet.cgi"
                    params = {"pbm": str(pbm), "pvid": str(pvid_str)}
                    _LOGGER.debug("Setze PVID: GET %s params=%s", url, params)
                    s.get(url, params=params, timeout=8)

            # Logout
            try:
                s.get(f"http://{self._ip}/Logout.htm", timeout=5)
            except Exception:
                pass

            return True
        except Exception as e:
            _LOGGER.exception("Fehler beim Anwenden des Profils %s auf %s: %s", phase, self._ip, e)
            return False
