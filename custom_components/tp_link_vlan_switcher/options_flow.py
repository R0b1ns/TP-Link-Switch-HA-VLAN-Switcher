import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN


class VlanSwitchOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for VLAN Switcher."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.switches = config_entry.options.get("switches", {})

    async def async_step_init(self, user_input=None):
        """Menu for options flow."""
        if user_input is not None:
            action = user_input["action"]
            if action == "add":
                return await self.async_step_add_switch()
            if action == "remove":
                return await self.async_step_remove_switch()
            if action == "finish":
                # <<<< important: this triggers update_listener + reload
                return self.async_create_entry(title="", data={"switches": self.switches})

        schema = vol.Schema(
            {
                vol.Required("action"): vol.In(
                    {
                        "add": "Neuen Profil-Switch hinzufügen",
                        "remove": "Vorhandenen Profil-Switch entfernen",
                        "finish": "Fertigstellen",
                    }
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_add_switch(self, user_input=None):
        """Add a new profile switch."""
        if user_input is not None:
            name = user_input["name"]
            self.switches[name] = {
                "vlans": {},
                "pvid": {},
            }
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required("name"): str,
            }
        )
        return self.async_show_form(step_id="add_switch", data_schema=schema)

    async def async_step_remove_switch(self, user_input=None):
        """Remove an existing profile switch."""
        if user_input is not None:
            name = user_input["name"]
            self.switches.pop(name, None)
            return await self.async_step_init()

        if not self.switches:
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required("name"): vol.In(list(self.switches.keys())),
            }
        )
        return self.async_show_form(step_id="remove_switch", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return VlanSwitchOptionsFlowHandler(config_entry)
