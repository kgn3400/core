"""The Messages log integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .component_api import ComponentApi
from .const import DOMAIN, LOGGER

PLATFORMS: list[Platform] = [Platform.SENSOR]


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class CommonData:
    """Common data."""

    coordinator: DataUpdateCoordinator
    component_api: ComponentApi


# The type alias needs to be suffixed with 'ConfigEntry'
type CommonConfigEntry = ConfigEntry[CommonData]


# ------------------------------------------------------------------
async def async_setup_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> bool:
    """Set up Pypi updates from a config entry."""

    coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=DOMAIN,
    )

    component_api: ComponentApi = ComponentApi(
        hass,
        coordinator,
        entry,
    )

    entry.runtime_data = CommonData(
        component_api=component_api,
        coordinator=coordinator,
    )

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_config_entry_first_refresh()

    return True


# ------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# ------------------------------------------------------------------
async def async_reload_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


# ------------------------------------------------------------------
async def update_listener(
    hass: HomeAssistant,
    config_entry: CommonConfigEntry,
) -> None:
    """Reload on config entry update."""

    await hass.config_entries.async_reload(config_entry.entry_id)
