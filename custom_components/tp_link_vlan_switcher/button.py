import logging
from homeassistant.components.button import ButtonEntity
from .entity_base import TPLinkSmartSwitchBaseEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up button entities for TP-Link VLAN Switch."""
    entities = [
        RebootButton(config_entry),
        ResetButton(config_entry),
    ]
    async_add_entities(entities)


class RebootButton(TPLinkSmartSwitchBaseEntity, ButtonEntity):
    """Button to reboot the switch."""

    _attr_name = "Reboot Switch"

    def __init__(self, config_entry):
        super().__init__(config_entry)
        self._attr_unique_id = f"{self._ip}_reboot"

    async def async_press(self) -> None:
        """Send reboot command to the switch."""
        ip = self._ip
        _LOGGER.debug("Reboot command sent to %s", ip)
        # TODO: Implementiere echten HTTP-Request


class ResetButton(TPLinkSmartSwitchBaseEntity, ButtonEntity):
    """Button to reset the switch."""

    _attr_name = "Reset Switch"

    def __init__(self, config_entry):
        super().__init__(config_entry)
        self._attr_unique_id = f"{self._ip}_reset"

    async def async_press(self) -> None:
        """Send reset command to the switch."""
        ip = self._ip
        _LOGGER.debug("Reset command sent to %s", ip)
        # TODO: Implementiere echten HTTP-Request
