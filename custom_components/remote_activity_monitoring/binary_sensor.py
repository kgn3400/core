"""Support for Pin alert."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import (
    Event,
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.helpers import entity_registry as er, issue_registry as ir, start
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COMPONENT_TYPE,
    CONF_ENTITY_IDS,
    DOMAIN,
    DOMAIN_NAME,
    LOGGER,
    TRANSLATION_KEY,
    ComponentType,
)
from .entity import ComponentEntity


# ------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry for Remote activity monitoring setup."""

    match entry.options[CONF_COMPONENT_TYPE]:
        case ComponentType.MAIN:
            pass
        case ComponentType.REMOTE:
            async_add_entities([RemoteAcitvityMonitorBinarySensor(hass, entry)])


# ------------------------------------------------------
# ------------------------------------------------------
class RemoteAcitvityMonitorBinarySensor(ComponentEntity, BinarySensorEntity):
    """Sensor class for Remote activity monitoring."""

    entity_list: list[RemoteAcitvityMonitorBinarySensor] = []

    # ------------------------------------------------------
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Binary sensor."""
        self.entry: ConfigEntry = entry
        self.hass = hass

        self.coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
            self.hass,
            LOGGER,
            name=DOMAIN,
            # update_interval=timedelta(minutes=1),
            update_method=self.async_refresh,
        )

        super().__init__(self.coordinator, entry)

        self.translation_key = TRANSLATION_KEY

        self.monitor_activity_on = False
        self.monitor_activity_name: str = ""
        self.monitor_activity_entity_id: str = ""
        self.monitor_activity_last_update: datetime = dt_util.now()

        registry = er.async_get(hass)
        self.monitor_activity_entities: list[str] = er.async_validate_entity_ids(
            registry, entry.options[CONF_ENTITY_IDS]
        )

        self.hass.services.async_register(
            DOMAIN,
            "get_remotes",
            self.async_get_remotes,
            supports_response=SupportsResponse.ONLY,
        )

    # ------------------------------------------------------------------
    async def async_get_remotes(self, call: ServiceCall) -> ServiceResponse:
        """Get active remotes."""

        return {
            "remotes": [
                {
                    "name": item.name,
                    "entity_id": item.entity_id,
                }
                for item in self.entity_list
            ]
        }

    # ------------------------------------------------------
    async def async_will_remove_from_hass(self) -> None:
        """When removed from hass."""
        RemoteAcitvityMonitorBinarySensor.entity_list.remove(self)

    # ------------------------------------------------------
    @callback
    async def sensor_state_listener(
        self,
        event: Event[EventStateChangedData],
    ) -> None:
        """Handle state changes on the observed device."""
        if (tmp_state := event.data["new_state"]) is None:
            return

        self.monitor_activity_on = bool(tmp_state.state == STATE_ON)
        self.monitor_activity_name = tmp_state.name
        self.monitor_activity_entity_id = tmp_state.entity_id
        self.monitor_activity_last_update = dt_util.now()
        await self.coordinator.async_refresh()

    # ------------------------------------------------------
    async def async_added_to_hass(self) -> None:
        """Complete device setup after being added to hass."""

        # await super().async_added_to_hass()

        await self.coordinator.async_config_entry_first_refresh()

        RemoteAcitvityMonitorBinarySensor.entity_list.append(self)

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                self.monitor_activity_entities,
                self.sensor_state_listener,
            )
        )
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

        self.async_on_remove(start.async_at_started(self.hass, self.hass_started))

    # ------------------------------------------------------
    async def async_verify_entity_exist(
        self,
    ) -> bool:
        """Verify entity exist."""

        # state: State | None = self.hass.states.get(
        #     self.entry.options.get(CONF_ENTITY_ID)
        # )

        # if state is None:
        #     await self.async_create_issue_entity(
        #         self.entry.options.get(CONF_ENTITY_ID),
        #         TRANSLATION_KEY_MISSING_ENTITY,
        #     )
        #     self.coordinator.update_interval = None
        #     return False

        return True

    # ------------------------------------------------------
    async def async_refresh(self) -> None:
        """Refresh."""

    # ------------------------------------------------------
    async def hass_started(self, _event: Event) -> None:
        """Hass started."""

        if await self.async_verify_entity_exist():
            pass

    # ------------------------------------------------------------------
    async def async_create_issue_entity(
        self, entity_id: str, translation_key: str
    ) -> None:
        """Create issue on entity."""

        ir.async_create_issue(
            self.hass,
            DOMAIN,
            DOMAIN_NAME + datetime.now().isoformat(),
            issue_domain=DOMAIN,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=translation_key,
            translation_placeholders={
                "entity": entity_id,
                "state_updated_helper": self.entity_id,
            },
        )

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name.

        Returns:
            str: Name of sensor

        """
        return self.entry.title

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique id

        """

        return self.entry.entry_id

    # ------------------------------------------------------
    @property
    def icon(self) -> str:
        """Icon.

        Returns:
            str: Icon name

        """

        if self.monitor_activity_on:
            return "mdi:alert-plus-outline"

        return "mdi:alert-outline"

    # ------------------------------------------------------
    @property
    def is_on(self) -> bool:
        """Get the state."""

        return self.monitor_activity_on

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: _description_

        """

        return {
            "last_monitor_activity_name": self.monitor_activity_name,
            "last_monitor_activity_entity_id": self.monitor_activity_entity_id,
            "last_monitor_activity_last_update": self.monitor_activity_last_update.isoformat(),
        }

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
