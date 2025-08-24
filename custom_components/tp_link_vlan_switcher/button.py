from homeassistant.components.button import ButtonEntity
from .entity_base import TPLinkSmartSwitchBaseEntity

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

    async def async_press(self) -> None:
        """Send reboot command to the switch."""
        ip = self._ip
        # Hier kommt dein HTTP-Call rein, z.B. POST /reboot.cgi
        print(f"Reboot command sent to {ip}")
        # TODO: Implementiere echten HTTP-Request


class ResetButton(TPLinkSmartSwitchBaseEntity, ButtonEntity):
    """Button to reset the switch."""

    _attr_name = "Reset Switch"

    async def async_press(self) -> None:
        """Send reset command to the switch."""
        ip = self._ip
        # Hier kommt dein HTTP-Call rein, z.B. POST /reset.cgi
        print(f"Reset command sent to {ip}")
        # TODO: Implementiere echten HTTP-Request
