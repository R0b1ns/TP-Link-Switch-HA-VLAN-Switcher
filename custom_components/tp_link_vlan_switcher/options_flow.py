import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_VLANS, CONF_PVID


class VlanSwitchOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for VLAN/PVID Switch definitions."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.switches = dict(config_entry.options.get("switches", {}))
        self.current_name = None
        self.current_vlans = {}
        self.current_pvid = {}

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            action = user_input["action"]
            if action == "add_switch":
                return await self.async_step_add_switch_name()
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

    async def async_step_add_switch_name(self, user_input=None):
        if user_input is not None:
            self.current_name = user_input["name"]
            return await self.async_step_add_switch_vlans()

        schema = vol.Schema({
            vol.Required("name"): str,
        })
        return self.async_show_form(step_id="add_switch_name", data_schema=schema)

    async def async_step_add_switch_vlans(self, user_input=None):
        if user_input is not None:
            # Ports → VLAN ID
            self.current_vlans = {
                "turn_on": {1: user_input["on_vlan_port1"], 2: user_input["on_vlan_port2"]},
                "turn_off": {1: user_input["off_vlan_port1"], 2: user_input["off_vlan_port2"]},
            }
            return await self.async_step_add_switch_pvid()

        schema = vol.Schema({
            vol.Required("on_vlan_port1", default=1): int,
            vol.Required("on_vlan_port2", default=1): int,
            vol.Required("off_vlan_port1", default=0): int,
            vol.Required("off_vlan_port2", default=0): int,
        })
        return self.async_show_form(step_id="add_switch_vlans", data_schema=schema)

    async def async_step_add_switch_pvid(self, user_input=None):
        if user_input is not None:
            # PVID-ID → Ports (einfacher Input erstmal als Liste)
            self.current_pvid = {
                "turn_on": {user_input["on_pvid"]: [1, 2]},
                "turn_off": {user_input["off_pvid"]: [1, 2]},
            }

            self.switches[self.current_name] = {
                CONF_VLANS: self.current_vlans,
                CONF_PVID: self.current_pvid,
            }
            return await self.async_step_init()

        schema = vol.Schema({
            vol.Required("on_pvid", default=1): int,
            vol.Required("off_pvid", default=0): int,
        })
        return self.async_show_form(step_id="add_switch_pvid", data_schema=schema)