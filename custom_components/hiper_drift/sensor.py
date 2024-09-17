"""Support for Hiper."""

from __future__ import annotations

from homeassistant.components.sensor import (  # SensorDeviceClass,; SensorEntityDescription,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .component_api import ComponentApi
from .const import DOMAIN, TRANSLATION_KEY
from .entity import ComponentEntity


# ------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry for Hiper drift setup."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    component_api: ComponentApi = hass.data[DOMAIN][entry.entry_id]["component_api"]

    sensors = []

    sensors.append(HiperMsgSensor(coordinator, entry, component_api))

    async_add_entities(sensors)


# ------------------------------------------------------
# ------------------------------------------------------
class HiperMsgSensor(ComponentEntity, SensorEntity):
    """Sensor class Hiper."""

    # ------------------------------------------------------
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        component_api: ComponentApi,
    ) -> None:
        """Hiper msg sensor.

        Args:
            coordinator (DataUpdateCoordinator): _description_
            entry (ConfigEntry): _description_
            component_api (ComponentApi): _description_

        """
        super().__init__(coordinator, entry)

        self.component_api = component_api
        # self.coordinator = coordinator
        self._name = "Message"
        self._unique_id = "message"

        self.translation_key = TRANSLATION_KEY

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name.

        Returns:
            str: Name

        """
        return self._name

    @property
    def native_value(self) -> str | None:
        """Native value.

        Returns:
            str | None: Native value

        """
        return self.component_api.msg

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """

        attr: dict = {}

        attr["content"] = self.component_api.content if self.component_api.is_on else ""

        if self.component_api.last_updated is not None:
            attr["last_updated"] = self.component_api.last_updated

        return attr

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique id

        """
        return self._unique_id

    # ------------------------------------------------------
    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    # ------------------------------------------------------
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    # ------------------------------------------------------
    async def async_update(self) -> None:
        """Update the entity. Only used by the generic entity update service."""
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
