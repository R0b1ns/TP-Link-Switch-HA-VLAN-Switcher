from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, CONF_IP, CONF_DEVICE, CONF_USERNAME, CONF_PASSWORD


class TPLinkSmartSwitchBaseEntity(Entity):
    """Base entity with shared device info."""

    def __init__(self, config_entry):
        self._config_entry = config_entry
        self._ip = config_entry.data[CONF_IP]
        self._user = config_entry.data.get(CONF_USERNAME)
        self._pwd = config_entry.data.get(CONF_PASSWORD)
        self._device_info = config_entry.data.get(CONF_DEVICE, {})

    @property
    def device_info(self):
        mac = self._device_info.get("macStr")

        # mac kann ein String oder eine Liste sein
        if isinstance(mac, list):
            # z.B. nur das erste Element nutzen oder alle
            mac_set = {("mac", m) for m in mac}
        elif mac:
            mac_set = {("mac", mac)}
        else:
            mac_set = set()

        return DeviceInfo(
            identifiers = {(DOMAIN, self._ip)},
            name = self._device_info.get("descriStr", f"TP-Link Smart Switch {self._ip}"),
            connections = mac_set,
            manufacturer = "TP-Link",
            model = self._device_info.get("hardwareStr").split(" ", 1)[0],
            sw_version = self._device_info.get("firmwareStr"),
            hw_version = self._device_info.get("hardwareStr").split(" ", 1)[1],
            configuration_url=f"http://{self._ip}/"
        )
