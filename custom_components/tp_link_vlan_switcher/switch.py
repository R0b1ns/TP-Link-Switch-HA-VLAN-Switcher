import logging
from typing import Any, Dict
import requests

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify

from .const import DOMAIN, CONF_IP, CONF_USERNAME, CONF_PASSWORD, CONF_VLANS, CONF_PVID
from .entity_base import TPLinkSmartSwitchBaseEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    data = entry.data
    options = entry.options or {}

    switches: Dict[str, Dict[str, Any]] = options.get("switches", {})
    if not switches:
        _LOGGER.debug("[%s] Keine Switch-Profile in options -> keine Entitäten", entry.entry_id)
        return

    entities = []
    for name, cfg in switches.items():
        vlans = cfg.get(CONF_VLANS, {}) or {}
        pvid = cfg.get(CONF_PVID, {}) or {}
        entities.append(
            VLANProfileSwitch(
                config_entry=entry,
                name=name,
                vlans=vlans,
                pvid=pvid,
            )
        )
    async_add_entities(entities)

class VLANProfileSwitch(TPLinkSmartSwitchBaseEntity, SwitchEntity):
    def __init__(self, config_entry, name, vlans, pvid):
        super().__init__(config_entry)

        self._profile_name = name
        self._vlans = vlans        # {"turn_on": {...}, "turn_off": {...}}
        self._pvid = pvid          # {"turn_on": {...}, "turn_off": {...}}
        self._is_on = False

        self._attr_name = f"{name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{slugify(name)}"

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

    # --- Netzwerklogik (Login → VLAN → PVID → Logout). Hier minimal & robust. ---
    def _apply_profile(self, phase: str) -> bool:
        """phase = 'turn_on' oder 'turn_off'."""
        try:
            s = requests.Session()
            # 1) Login
            login = s.post(
                f"http://{self._ip}/logon.cgi",
                data={"username": self._user, "password": self._pwd, "cpassword": "", "logon": "Login"},
                timeout=8,
            )
            if login.status_code != 200:
                _LOGGER.error("Login fehlgeschlagen (%s): HTTP %s", self._ip, login.status_code)
                return False

            # --- VLAN anwenden (du implementierst bei Bedarf Details) ---
            # Erwartete Struktur self._vlans:
            # {"turn_on": {<port>: <state> ...}, "turn_off": {...}}
            vlan_cfg = self._vlans.get(phase, {})
            if vlan_cfg:
                # TODO: Hier deine reale VLAN-Logik einbauen
                _LOGGER.debug("Würde VLAN anwenden (%s): %s", phase, vlan_cfg)
                # Beispiel (kommentiert): s.get(f"http://{self._ip}/qvlanSet.cgi?...")

            # --- PVID anwenden ---
            # Erwartete Struktur self._pvid:
            # {"turn_on": {"<pvid>": [ports...]}, "turn_off": {...}}
            pvid_cfg = self._pvid.get(phase, {})
            if pvid_cfg:
                for pvid_str, ports in pvid_cfg.items():
                    pbm = 0
                    for p in ports:
                        # Port-Bitmaske berechnen (Port 1 -> Bit0)
                        if isinstance(p, int) and p >= 1:
                            pbm |= (1 << (p - 1))
                    url = f"http://{self._ip}/vlanPvidSet.cgi"
                    params = {"pbm": str(pbm), "pvid": str(pvid_str)}
                    _LOGGER.debug("Setze PVID: GET %s params=%s", url, params)
                    s.get(url, params=params, timeout=8)

            # 4) Logout (best effort)
            try:
                s.get(f"http://{self._ip}/Logout.htm", timeout=5)
            except Exception:
                pass

            return True
        except Exception as e:
            _LOGGER.exception("Fehler beim Anwenden des Profils %s auf %s: %s", phase, self._ip, e)
            return False
