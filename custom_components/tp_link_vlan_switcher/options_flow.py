import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_VLANS, CONF_PVID

class VlanSwitchOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for VLAN/PVID."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.vlans = dict(config_entry.options.get(CONF_VLANS, {}))
        self.pvid = dict(config_entry.options.get(CONF_PVID, {}))

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            action = user_input["action"]
            if action == "add_vlan":
                return await self.async_step_add_vlan()
            if action == "add_pvid":
                return await self.async_step_add_pvid()
            if action == "finish":
                return self.async_create_entry(
                    title="", data={CONF_VLANS: self.vlans, CONF_PVID: self.pvid}
                )

        schema = vol.Schema({
            vol.Required("action", default="finish"): vol.In(
                {
                    "add_vlan": "Neues VLAN hinzufügen",
                    "add_pvid": "Neue PVID hinzufügen",
                    "finish": "Speichern & Beenden",
                }
            )
        })
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_add_vlan(self, user_input=None):
        if user_input is not None:
            vid = str(user_input["vid"])
            turn_on = user_input["turn_on"]
            turn_off = user_input["turn_off"]
            self.vlans[vid] = {"turn_on": turn_on, "turn_off": turn_off}
            return await self.async_step_init()

        schema = vol.Schema({
            vol.Required("vid"): str,
            vol.Optional("turn_on", default={}): dict,
            vol.Optional("turn_off", default={}): dict,
        })
        return self.async_show_form(step_id="add_vlan", data_schema=schema)

    async def async_step_add_pvid(self, user_input=None):
        if user_input is not None:
            pvid_id = str(user_input["pvid_id"])
            turn_on = user_input["turn_on"]
            turn_off = user_input["turn_off"]
            self.pvid[pvid_id] = {"turn_on": turn_on, "turn_off": turn_off}
            return await self.async_step_init()

        schema = vol.Schema({
            vol.Required("pvid_id"): str,
            vol.Optional("turn_on", default=[]): [int],
            vol.Optional("turn_off", default=[]): [int],
        })
        return self.async_show_form(step_id="add_pvid", data_schema=schema)
