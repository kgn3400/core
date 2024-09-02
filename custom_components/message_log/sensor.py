"""Sensor for Message log."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import (  # SensorDeviceClass,; SensorEntityDescription,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, start
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .component_api import ComponentApi
from .const import (
    CONF_LISTEN_TO_TIMER_TRIGGER,
    CONF_MARKDOWN_MESSAGE_LIST_COUNT,
    CONF_RESTART_TIMER,
    CONF_SCROLL_MESSAGES_EVERY_MINUTES,
    DOMAIN,
    TRANSLATION_KEY,
    RefreshType,
)
from .entity import ComponentEntity
from .message_log_settings import MessageItemAttr
from .timer_trigger import TimerTrigger


# ------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor setup."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    component_api: ComponentApi = hass.data[DOMAIN][entry.entry_id]["component_api"]

    await component_api.settings.async_read_settings()

    sensors = []

    sensors.append(MessageLastSensor(hass, coordinator, entry, component_api))
    sensors.append(MessageScrollSensor(hass, coordinator, entry, component_api))

    async_add_entities(sensors)


# ------------------------------------------------------
# ------------------------------------------------------
class MessageLastSensor(ComponentEntity, SensorEntity):
    """Sensor class for Last Message."""

    # ------------------------------------------------------
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        component_api: ComponentApi,
    ) -> None:
        """Last Message sensor."""

        super().__init__(coordinator, entry)

        self.component_api = component_api
        self.coordinator = coordinator
        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry

        self._name = "Last message"
        self._unique_id = "last_message"
        self.translation_key = TRANSLATION_KEY

        # self._attr_has_entity_name = True
        # self._attr_translation_key = "last_message"

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name."""

        return self._name

    # ------------------------------------------------------
    @property
    def icon(self) -> str:
        """Icon."""

        return self.component_api.message_last_icon

    # ------------------------------------------------------
    @property
    def native_value(self) -> str:
        """Native value."""

        return self.component_api.message_last

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes."""

        attr: dict = {}

        if self.component_api.message_level_last:
            attr["message_level_last"] = self.component_api.message_level_last

        if len(self.component_api.settings.message_list) > 0:
            attr["message_last_added_at"] = self.component_api.settings.message_list[
                0
            ].added_at.isoformat()

        if self.component_api.highest_message_level:
            attr["highest__message_level"] = self.component_api.highest_message_level

        if self.component_api.markdown:
            attr["markdown"] = self.component_api.markdown

        if self.component_api.markdown_message_list:
            attr["markdown_list"] = self.component_api.markdown_message_list

        if self.component_api.markdown_message_settings:
            attr["markdown_settings"] = self.component_api.markdown_message_settings

        message_list_attr: list[MessageItemAttr] = [
            MessageItemAttr(
                item.message,
                item.message_level,
                item.icon,
                item.notify,
                item.added_at,
            )
            for item in self.component_api.settings.message_list
        ]
        attr["message_list"] = message_list_attr[
            : int(self.entry.options.get(CONF_MARKDOWN_MESSAGE_LIST_COUNT, 10))
        ]

        return attr

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique  id

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

        self.hass.bus.async_listen(
            dr.EVENT_DEVICE_REGISTRY_UPDATED,
            self._handle_device_registry_updated,
        )
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------
    @callback
    async def _handle_device_registry_updated(
        self, event: Event[dr.EventDeviceRegistryUpdatedData]
    ) -> None:
        """Handle when device registry updated."""

        if event.data["action"] == "remove":
            self.component_api.settings.async_remove_settings()


# ------------------------------------------------------
# ------------------------------------------------------
class MessageScrollSensor(ComponentEntity, SensorEntity):
    """Sensor class for Message scroll."""

    # ------------------------------------------------------
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        component_api: ComponentApi,
    ) -> None:
        """Scroll Message sensor."""

        super().__init__(coordinator, entry)

        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry
        self.component_api = component_api
        self.coordinator = coordinator

        self.refresh_type: RefreshType = RefreshType.NORMAL

        self._name = "Scroll message"
        self._unique_id = "scroll_message"

        self.translation_key = TRANSLATION_KEY

        # self._attr_has_entity_name = True
        # self._attr_translation_key = "scroll_message"

        if self.entry.options.get(CONF_LISTEN_TO_TIMER_TRIGGER, ""):
            self.refresh_type = RefreshType.LISTEN_TO_TIMER_TRIGGER
            self.timer_trigger = TimerTrigger(
                self,
                self.entry.options.get(CONF_LISTEN_TO_TIMER_TRIGGER, ""),
                self.async_handle_timer_finished,
                self.entry.options.get(CONF_RESTART_TIMER, ""),
            )
            self.coordinator.update_interval = None

    # ------------------------------------------------------------------
    async def async_handle_timer_finished(self, error: bool) -> None:
        """Handle timer finished."""

        if error:
            self.refresh_type = RefreshType.NORMAL
            self.coordinator.update_interval = timedelta(
                minutes=self.entry.options.get(CONF_SCROLL_MESSAGES_EVERY_MINUTES, 1)
            )

        if self.refresh_type == RefreshType.LISTEN_TO_TIMER_TRIGGER:
            await self.coordinator.async_refresh()

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name."""

        return self._name

    # ------------------------------------------------------
    @property
    def icon(self) -> str:
        """Icon."""

        return self.component_api.message_scroll_icon

    # ------------------------------------------------------
    @property
    def native_value(self) -> str:
        """Native value."""

        return self.component_api.message_scroll

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes."""

        return {}

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique  id

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

        self.async_on_remove(start.async_at_started(self.hass, self.async_hass_started))

    # ------------------------------------------------------
    async def async_hass_started(self, _event: Event) -> None:
        """Hass started."""

        if self.refresh_type == RefreshType.NORMAL:
            self.coordinator.update_interval = timedelta(
                minutes=self.entry.options.get(CONF_SCROLL_MESSAGES_EVERY_MINUTES, 1)
            )
        elif self.refresh_type == RefreshType.LISTEN_TO_TIMER_TRIGGER:
            if not await self.timer_trigger.async_validate_timer():
                self.coordinator.update_interval = timedelta(
                    minutes=self.entry.options.get(
                        CONF_SCROLL_MESSAGES_EVERY_MINUTES, 1
                    )
                )
                self.refresh_type = RefreshType.NORMAL
