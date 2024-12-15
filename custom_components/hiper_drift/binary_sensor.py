"""Support for Hiper dK."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CommonConfigEntry
from .component_api import ComponentApi
from .const import TRANSLATION_KEY
from .entity import ComponentEntity


# ------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: CommonConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry for Hiper setup."""

    sensors = []

    sensors.append(HiperBinarySensor(entry))

    async_add_entities(sensors)


# ------------------------------------------------------
# ------------------------------------------------------
class HiperBinarySensor(ComponentEntity, BinarySensorEntity):
    """Sensor class for Hiper."""

    _attr_translation_key = "hiper_drift"

    # ------------------------------------------------------
    def __init__(
        self,
        entry: CommonConfigEntry,
    ) -> None:
        """Hiper binary sensor.

        Args:
            coordinator (DataUpdateCoordinator): _description_
            entry (ConfigEntry): _description_
            component_api (ComponentApi): _description_

        """
        super().__init__(entry.runtime_data.coordinator, entry)
        self.entry: CommonConfigEntry = entry

        self.component_api: ComponentApi = entry.runtime_data.component_api
        # self.coordinator = coordinator

        self._name = "Status"
        self._unique_id = "status"
        self.translation_key = TRANSLATION_KEY

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name.

        Returns:
            str: Name

        """
        return self._name

    # ------------------------------------------------------
    @property
    def is_on(self) -> bool:
        """Get the state."""

        return self.component_api.is_on

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """

        attr: dict = {}

        attr["message"] = self.component_api.msg if self.component_api.is_on else ""

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
