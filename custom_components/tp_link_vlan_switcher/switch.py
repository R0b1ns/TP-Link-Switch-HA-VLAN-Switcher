from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up VLAN switches dynamically from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    options = entry.options.get("switches", {})

    # Add new switches
    new_entities = []
    for name, cfg in options.items():
        if name not in hass.data[DOMAIN][entry.entry_id]:
            switch = VlanProfileSwitch(name, entry.entry_id, cfg)
            hass.data[DOMAIN][entry.entry_id][name] = switch
            new_entities.append(switch)

    if new_entities:
        async_add_entities(new_entities, update_before_add=True)

    # Remove switches that no longer exist
    to_remove = [
        name for name in hass.data[DOMAIN][entry.entry_id]
        if name not in options
    ]
    for name in to_remove:
        switch = hass.data[DOMAIN][entry.entry_id].pop(name)
        await switch.async_remove()

class VlanProfileSwitch(SwitchEntity):
    """Representation of a VLAN switch."""

    def __init__(self, name: str, entry_id: str, cfg: dict):
        self._attr_name = f"VLAN {name}"
        self._attr_unique_id = f"{entry_id}_{name}"
        self._is_on = False
        self._cfg = cfg

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        self.async_write_ha_state()
