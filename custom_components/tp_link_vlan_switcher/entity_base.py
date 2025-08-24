from homeassistant.helpers.entity import Entity
from .const import DOMAIN, CONF_IP, CONF_DEVICE

class TPLinkSmartSwitchBaseEntity(Entity):
    """Base entity with shared device info."""

    def __init__(self, config_entry):
        self._config_entry = config_entry
        self._ip = config_entry.data[CONF_IP]
        self._device_info = config_entry.data.get(CONF_DEVICE, {})

    @property
    def device_info(self):
        info = {
            "identifiers": {(DOMAIN, self._ip)},
            "name": self._device_info.get("descriStr", f"VLAN Switch {self._ip}"),
            "manufacturer": "TP-Link",
            "model": self._device_info.get("hardwareStr", "").split(" ")[0] if self._device_info.get(
                "hardwareStr") else None,
            "sw_version": self._device_info.get("firmwareStr"),
            "hw_version": self._device_info.get("hardwareStr", "").split(" ")[1] if self._device_info.get(
                "hardwareStr") else None,
        }
        mac = self._device_info.get("macStr")
        if mac:
            info["connections"] = {("mac", mac)}
        return info