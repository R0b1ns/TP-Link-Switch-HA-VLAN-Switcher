import json
import voluptuous as vol
from homeassistant import config_entries
from .const import CONF_VLANS, CONF_PVID

class VlanSwitchOptionsFlowHandler(config_entries.OptionsFlow):
    """OptionsFlow: Switch-Profile (Name + VLAN/PVID) verwalten."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.switches = dict(config_entry.options.get("switches", {}))

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            action = user_input["action"]
            if action == "add_switch":
                return await self.async_step_add_switch()
            if action == "finish":
                # Speichern -> __init__-Update-Listener triggert Reload, Entitäten werden neu erstellt
                return self.async_create_entry(title="", data={"switches": self.switches})

        schema = vol.Schema({
            vol.Required("action", default="finish"): vol.In({
                "add_switch": "Neuen Profil-Switch hinzufügen",
                "finish": "Speichern & Beenden",
            })
        })
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_add_switch(self, user_input=None):
        errors = {}
        if user_input is not None:
            name = user_input["name"].strip()
            try:
                vlans = json.loads(user_input["vlans_json"]) if user_input.get("vlans_json") else {}
                pvid = json.loads(user_input["pvid_json"]) if user_input.get("pvid_json") else {}
                # Minimale Validierung
                if not isinstance(vlans, dict) or not isinstance(pvid, dict):
                    errors["base"] = "invalid_json"
                else:
                    self.switches[name] = {CONF_VLANS: vlans, CONF_PVID: pvid}
                    return await self.async_step_init()
            except Exception:
                errors["base"] = "invalid_json"

        schema = vol.Schema({
            vol.Required("name", description={"name": "Name der Entität"}): str,
            vol.Optional("vlans_json", description={"name": "VLAN-Konfig (JSON)"}): str,
            vol.Optional("pvid_json", description={"name": "PVID-Konfig (JSON)"}): str,
        })
        return self.async_show_form(step_id="add_switch", data_schema=schema, errors=errors)
