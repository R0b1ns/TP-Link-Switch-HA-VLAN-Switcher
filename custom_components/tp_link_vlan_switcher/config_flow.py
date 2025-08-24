import voluptuous as vol
import json
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_IP, CONF_USERNAME, CONF_PASSWORD, CONF_VLANS


class VlanSwitchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_IP], data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_IP): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return VlanSwitchOptionsFlowHandler(config_entry)


class VlanSwitchOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # try parsing VLAN JSON
            vlans = []
            try:
                vlans = json.loads(user_input[CONF_VLANS])
            except Exception as e:
                errors = {"base": "invalid_json"}
                return self.async_show_form(
                    step_id="init",
                    data_schema=vol.Schema({
                        vol.Required(CONF_VLANS, default=user_input[CONF_VLANS]): str,
                    }),
                    errors=errors
                )
            return self.async_create_entry(title="", data={CONF_VLANS: vlans})

        # show empty or current vlans as json
        current = self.config_entry.options.get(CONF_VLANS, [])
        import json
        current_json = json.dumps(current, indent=2)
        schema = vol.Schema({
            vol.Required(CONF_VLANS, default=current_json): str,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
