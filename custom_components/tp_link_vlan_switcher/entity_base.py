from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, CONF_IP, CONF_DEVICE

class TPLinkSmartSwitchBaseEntity(Entity):
    """Base entity with shared device info."""

    def __init__(self, config_entry):
        self._config_entry = config_entry
        self._ip = config_entry.data[CONF_IP]
        self._device_info = config_entry.data.get(CONF_DEVICE, {})

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers = {(DOMAIN, self._ip)},
            name = self._device_info.get("descriStr", f"TP-Link Smart Switch {self._ip}"),
            connections = {("mac", self._device_info.get("macStr"))} if self._device_info.get("macStr") else None,
            manufacturer = "TP-Link",
            model = self._device_info.get("hardwareStr").split(" ", 1)[0],
            sw_version = self._device_info.get("firmwareStr"),
            hw_version = self._device_info.get("hardwareStr").split(" ", 1)[1],
        )
