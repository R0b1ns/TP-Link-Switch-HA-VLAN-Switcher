import logging
from typing import Any, Dict

from homeassistant.components.switch import SwitchEntity
from homeassistant.util import slugify

from .const import DOMAIN, CONF_VLANS, CONF_PVID
from .entity_base import TPLinkSmartSwitchBaseEntity
from .tp_link_connector import TPLinkConnector, Phase

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
    def __init__(self, config_entry, name: str, vlans: dict, pvid: dict):
        super().__init__(config_entry)

        self._profile_name = name
        self._vlans = vlans        # {"turn_on": [...], "turn_off": [...]}
        self._pvid = pvid          # {"turn_on": {...}, "turn_off": {...}}
        self._is_on = False

        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{slugify(name)}"

        # TPLinkConnector initialisieren
        self._connector = TPLinkConnector(self._ip, self._user, self._pwd)

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

    # async def async_update(self):
    #     """HA calls this to refresh the state."""
    #     await self.hass.async_add_executor_job(self.update_status)
    #     self.async_write_ha_state()
    #
    # def update_status(self):
    #     """
    #     Read current switch configuration and update self._is_on.
    #     If no status-API is available, fallback to last known state.
    #     """
    #     try:
    #         self._connector._start_session()
    #         # TODO: Hier echte Status-Abfrage einbauen, z.B.:
    #         # response = self._connector._session.get(f"http://{self._ip}/status.cgi")
    #         # parse response -> self._is_on = True/False
    #         # Fallback: Beibehalten des letzten bekannten Status
    #     except Exception as e:
    #         _LOGGER.warning("Could not read switch status for '%s': %s", self._profile_name, e)
    #     finally:
    #         self._connector._close_session()

    # ---------------------- Profile anwenden ----------------------
    def _apply_profile(self, phase: Phase) -> bool:
        """Apply VLAN + PVID using TPLinkConnector."""
        try:
            return self._connector.apply_profile(self._vlans, self._pvid, phase)
        except Exception as e:
            _LOGGER.exception("Fehler beim Anwenden des Profils %s auf %s: %s", phase, self._profile_name, e)
            return False
