import json
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_PORTS


class VlanSwitchOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for VLAN Switcher."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.switches = config_entry.options.get("switches", {})
        self._edit_name = None

        self.port_count = config_entry.data.get(CONF_PORTS)

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
        return self.async_create_entry(title="", options={"switches": self.switches})

    # -------------------------------
    # ADD
    # -------------------------------
    async def async_step_add_switch(self, user_input=None):
        """Add a new profile switch."""
        if user_input is not None:
            if not user_input.get("confirm"):
                return self.async_show_form(
                    step_id="add_switch",
                    data_schema=self._get_add_schema(user_input),
                    errors={"base": "confirm_required"},
                )

            try:
                name = user_input["name"]
                vlans = json.loads(user_input["vlans"])
                pvid = json.loads(user_input["pvid"])
            except (ValueError, KeyError):
                return self.async_show_form(
                    step_id="add_switch",
                    data_schema=self._get_add_schema(user_input),
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

    def _get_add_schema(self, user_input=None):
        """Return schema for adding a switch."""
        if user_input is None:
            user_input = {}

        vlan_template = """{
  "turn_on": [
    {
      "vid": 1,
      "vname": "Home network",
      "ports": {
        "3": 2
      }
    },
    {
      "vid": 20,
      "vname": "Guest network",
      "ports": {
        "3": 0
      }
    }
  ],
  "turn_off": [
    {
      "vid": 1,
      "vname": "Home network",
      "ports": {
        "3": 0
      }
    },
    {
      "vid": 20,
      "vname": "Guest network",
      "ports": {
        "3": 2
      }
    }
  ]
}"""
        pvid_template = """{
  "turn_on": {
    "10": [5,6]
  },
  "turn_off": {
    "1": [1,2,3,6,7,8]
  }
}"""

        return vol.Schema(
            {
                vol.Required("name", default=user_input.get("name", "")): str,
                vol.Required("vlans", default=user_input.get("vlans", vlan_template), description="state = 0 (Untagged), state = 1 (Tagged), state = 2 (Not Member)"): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Required("pvid", default=user_input.get("pvid", pvid_template), description="You can define multiple PVID configurations"): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Required("confirm", default=False): bool,
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
        """Edit details of a switch (vlans, pvid)."""
        current = self.switches[self._edit_name]

        if user_input is not None:
            # Dummy-Infofelder entfernen, bevor wir speichern
            user_input.pop("info_vlans", None)
            user_input.pop("info_pvid", None)

            if not user_input.get("confirm"):
                return self.async_show_form(
                    step_id="edit_switch_details",
                    data_schema=self._get_edit_schema(current, user_input),
                    errors={"base": "confirm_required"},
                )

            try:
                vlans = json.loads(user_input["vlans"])
                pvid = json.loads(user_input["pvid"])
            except (ValueError, KeyError):
                return self.async_show_form(
                    step_id="edit_switch_details",
                    data_schema=self._get_edit_schema(current, user_input),
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

    def _get_edit_schema(self, current: dict, user_input: dict = None):
        """Return schema for editing a switch."""
        if user_input is None:
            user_input = {}

        vlan_default = user_input.get("vlans") or json.dumps(current.get("vlans", {}), indent=2)
        pvid_default = user_input.get("pvid") or json.dumps(current.get("pvid", {}), indent=2)
        confirm_default = user_input.get("confirm", False)

        return vol.Schema(
            {
                # Optionales Dummy-Feld für Info (nur lesen, wird ignoriert)
                vol.Optional(
                    "info_vlans",
                    default="Definiere VLANs im JSON-Format.\nstate = 0 (Untagged), state = 1 (Tagged), state = 2 (Not Member)",
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),

                vol.Required(
                    "vlans",
                    default=vlan_default,
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),

                vol.Optional(
                    "info_pvid",
                    default="Definiere PVID-Zuweisungen im JSON-Format.",
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),

                vol.Required(
                    "pvid",
                    default=pvid_default,
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),

                vol.Required(
                    "confirm",
                    default=confirm_default,
                ): bool,
            }
        )

    # -------------------------------
    # ENTRYPOINT
    # -------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return VlanSwitchOptionsFlowHandler(config_entry)
