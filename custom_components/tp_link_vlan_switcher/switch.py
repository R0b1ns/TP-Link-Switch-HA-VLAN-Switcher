from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up profile switches from a config entry."""
    switches = []

    options = entry.options.get("switches", {})
    for name, cfg in options.items():
        switches.append(VlanProfileSwitch(name, entry.entry_id, cfg))

    async_add_entities(switches, update_before_add=True)


class VlanProfileSwitch(SwitchEntity):
    """Representation of a VLAN Profile switch."""

    def __init__(self, name: str, entry_id: str, cfg: dict):
        self._attr_name = f"VLAN {name}"
        self._attr_unique_id = f"{entry_id}_{name}"
        self._is_on = False
        self._cfg = cfg

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        # TODO: VLAN + PVID apply logic here
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        # TODO: VLAN + PVID revert logic here
        self._is_on = False
        self.async_write_ha_state()
