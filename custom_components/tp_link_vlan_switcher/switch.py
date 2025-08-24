from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType
from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up VLAN switches under a single device."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    # Entferne alte Entitäten
    for switch in list(hass.data[DOMAIN][entry.entry_id].values()):
        await switch.async_remove()
    hass.data[DOMAIN][entry.entry_id] = {}

    # Optionen durchgehen und neue Switches erstellen
    options = entry.options.get("switches", {})
    new_entities = []

    for name, cfg in options.items():
        switch = VlanProfileSwitch(name, entry.entry_id, cfg, entry)
        hass.data[DOMAIN][entry.entry_id][name] = switch
        new_entities.append(switch)

    if new_entities:
        async_add_entities(new_entities, update_before_add=True)


class VlanProfileSwitch(SwitchEntity):
    """Representation of a VLAN switch under a device."""

    def __init__(self, name: str, entry_id: str, cfg: dict, entry: ConfigEntry):
        self._attr_name = f"VLAN {name}"
        self._attr_unique_id = f"{entry_id}_{name}"
        self._is_on = False
        self._cfg = cfg
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "VLAN Device",
            "manufacturer": "TP-Link",
            "model": "VLAN Switcher",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        self.async_write_ha_state()
