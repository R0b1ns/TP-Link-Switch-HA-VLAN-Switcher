import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_VLANS, CONF_PVID

class VlanSwitchOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for VLAN/PVID Switch definitions."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        # switches: {"switch_name": {"vlans": {...}, "pvid": {...}}}
        self.switches = dict(config_entry.options.get("switches", {}))

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            action = user_input["action"]
            if action == "add_switch":
                return await self.async_step_add_switch()
            if action == "finish":
                return self.async_create_entry(title="", data={"switches": self.switches})

        schema = vol.Schema({
            vol.Required("action", default="finish"): vol.In(
                {
                    "add_switch": "Neuen Switch hinzufügen",
                    "finish": "Speichern & Beenden",
                }
            )
        })
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_add_switch(self, user_input=None):
        if user_input is not None:
            name = user_input["name"]
            vlans = user_input["vlans"]
            pvid = user_input["pvid"]

            self.switches[name] = {
                CONF_VLANS: vlans,
                CONF_PVID: pvid,
            }
            return await self.async_step_init()

        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required(CONF_VLANS, description={"name": "VLAN Konfiguration (JSON)"}): str,
            vol.Required(CONF_PVID, description={"name": "PVID Konfiguration (JSON)"}): str,
        })
        return self.async_show_form(step_id="add_switch", data_schema=schema)
