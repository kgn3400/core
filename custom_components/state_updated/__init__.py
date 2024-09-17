"""The State updated integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device import (
    async_remove_stale_devices_links_keep_current_device,
)

from .component_api import ComponentApi
from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]


# ------------------------------------------------------------------
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up State updates from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    component_api: ComponentApi = ComponentApi(
        hass,
        entry,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "component_api": component_api,
    }

    entry.async_on_unload(entry.add_update_listener(update_listener))

    async_remove_stale_devices_links_keep_current_device(
        hass,
        entry.entry_id,
        entry.options.get(CONF_DEVICE_ID),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


# ------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# ------------------------------------------------------------------
async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


# ------------------------------------------------------------------
async def update_listener(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Reload on config entry update."""

    component_api: ComponentApi = hass.data[DOMAIN][config_entry.entry_id][
        "component_api"
    ]

    if component_api.supress_update_listener:
        component_api.supress_update_listener = False
        return

    await hass.config_entries.async_reload(config_entry.entry_id)
