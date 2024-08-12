"""Base entity for the My dyn ip integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, DOMAIN_NAME


class ComponentEntity(CoordinatorEntity[DataUpdateCoordinator], Entity):
    """Defines a My dyn ip entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the My dyn ip entity."""
        super().__init__(coordinator=coordinator)
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, DOMAIN_NAME)},
            manufacturer="KGN",
            suggested_area="",
            sw_version="1.0.2",
            name=DOMAIN_NAME,
        )
