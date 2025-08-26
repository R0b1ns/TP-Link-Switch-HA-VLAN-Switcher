import json
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN


class VlanSwitchOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for VLAN Switcher."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.switches = config_entry.options.get("switches", {})
        self._edit_name = None

    async def async_step_init(self, user_input=None):
        """Menu for options flow."""
        if user_input is not None:
            action = user_input["action"]
            if action == "add":
                return await self.async_step_add_switch()
            if action == "remove":
                return await self.async_step_remove_switch()
            if action == "edit":
                return await self.async_step_edit_switch()

        schema = vol.Schema(
            {
                vol.Required("action"): vol.In(
                    {
                        "add": "Neuen Profil-Switch hinzufügen",
                        "remove": "Vorhandenen Profil-Switch entfernen",
                        "edit": "Vorhandenen Profil-Switch bearbeiten",
                    }
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def _finish(self):
        """Create the options entry after any change."""
        return self.async_create_entry(title="", data={"switches": self.switches})

    # -------------------------------
    # ADD
    # -------------------------------
    async def async_step_add_switch(self, user_input=None):
        """Add a new profile switch."""
        if user_input is not None:
            try:
                name = user_input["name"]
                vlans = json.loads(user_input["vlans"])
                pvid = json.loads(user_input["pvid"])
            except (ValueError, KeyError):
                return self.async_show_form(
                    step_id="add_switch",
                    data_schema=self._get_add_schema(),
                    errors={"base": "invalid_json"},
                )

            self.switches[name] = {
                "vlans": vlans,
                "pvid": pvid,
            }
            return await self._finish()

        return self.async_show_form(
            step_id="add_switch",
            data_schema=self._get_add_schema(),
        )

    def _get_add_schema(self):
        """Return schema for adding a switch."""
        vlan_template = """{
  "10": "Office",
  "20": "IoT"
}"""
        pvid_template = """{
  "1": "Default",
  "10": "Office-Port"
}"""

        return vol.Schema(
            {
                vol.Required("name"): str,
                vol.Required("vlans", default=vlan_template): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Required("pvid", default=pvid_template): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
            }
        )

    # -------------------------------
    # REMOVE
    # -------------------------------
    async def async_step_remove_switch(self, user_input=None):
        """Remove an existing profile switch."""
        if user_input is not None:
            name = user_input["name"]
            self.switches.pop(name, None)
            return await self._finish()

        if not self.switches:
            return await self._finish()

        schema = vol.Schema(
            {
                vol.Required("name"): vol.In(list(self.switches.keys())),
            }
        )
        return self.async_show_form(step_id="remove_switch", data_schema=schema)

    # -------------------------------
    # EDIT
    # -------------------------------
    async def async_step_edit_switch(self, user_input=None):
        """Choose which switch to edit."""
        if user_input is not None:
            self._edit_name = user_input["name"]
            return await self.async_step_edit_switch_details()

        if not self.switches:
            return await self._finish()

        schema = vol.Schema(
            {
                vol.Required("name"): vol.In(list(self.switches.keys())),
            }
        )
        return self.async_show_form(step_id="edit_switch", data_schema=schema)

    async def async_step_edit_switch_details(self, user_input=None):
        """Edit details of a switch (vlans and pvid)."""
        current = self.switches[self._edit_name]

        if user_input is not None:
            try:
                vlans = json.loads(user_input["vlans"])
                pvid = json.loads(user_input["pvid"])
            except (ValueError, KeyError):
                return self.async_show_form(
                    step_id="edit_switch_details",
                    data_schema=self._get_edit_schema(current),
                    errors={"base": "invalid_json"},
                )

            self.switches[self._edit_name] = {
                "vlans": vlans,
                "pvid": pvid,
            }
            return await self._finish()

        return self.async_show_form(
            step_id="edit_switch_details",
            data_schema=self._get_edit_schema(current),
        )

    def _get_edit_schema(self, current: dict):
        """Return schema for editing a switch."""
        return vol.Schema(
            {
                vol.Required("vlans", default=json.dumps(current.get("vlans", {}), indent=2)): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Required("pvid", default=json.dumps(current.get("pvid", {}), indent=2)): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
            }
        )

    # -------------------------------
    # ENTRYPOINT
    # -------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return VlanSwitchOptionsFlowHandler(config_entry)
