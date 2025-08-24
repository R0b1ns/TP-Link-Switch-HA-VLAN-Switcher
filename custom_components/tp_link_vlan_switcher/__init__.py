from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform
from .const import DOMAIN, PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up TP-Link VLAN Switcher from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

    async def _update_listener(hass: HomeAssistant, updated_entry: ConfigEntry):
        """Reload when config entry options change."""
        await hass.config_entries.async_reload(updated_entry.entry_id)

    # async def _update_listener(hass: HomeAssistant, updated_entry: ConfigEntry):
    #     """Reload when config entry options change."""
    #     # Trigger the platform to setup again
    #     for platform in PLATFORMS:
    #         hass.async_create_task(
    #             hass.config_entries.async_forward_entry_setup(updated_entry, platform)
    #         )

    # register listener for options updates
    entry.async_on_unload(entry.add_update_listener(_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
