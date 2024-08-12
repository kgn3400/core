"""Sensor for Lotto dK."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import (  # SensorDeviceClass,; SensorEntityDescription,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import start
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .component_api import ComponentApi, LottoTypes
from .const import (
    CONF_LISTEN_TO_TIMER_TRIGGER,
    CONF_RESTART_TIMER,
    DOMAIN,
    TRANSLATION_KEY,
    RefreshType,
)
from .entity import ComponentEntity
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

    sensors = []

    # Euro jackpot
    if component_api.get_euro_jackpot:
        sensors.append(
            LottoSensor(
                hass, coordinator, entry, component_api, LottoTypes.EURO_JACKPOT
            )
        )

    # Lotto
    if component_api.get_lotto:
        sensors.append(
            LottoSensor(hass, coordinator, entry, component_api, LottoTypes.LOTTO)
        )

    # Viking Lotto
    if component_api.get_viking_lotto:
        sensors.append(
            LottoSensor(
                hass, coordinator, entry, component_api, LottoTypes.VIKING_LOTTO
            )
        )

    sensors.append(LottoScrollSensor(hass, coordinator, entry, component_api))

    async_add_entities(sensors)


# ------------------------------------------------------
# ------------------------------------------------------
class LottoSensor(ComponentEntity, SensorEntity):
    """Sensor class for lotto."""

    # ------------------------------------------------------
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        component_api: ComponentApi,
        lotto_type: LottoTypes,
    ) -> None:
        """Lotto sensor."""

        super().__init__(coordinator, entry)

        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry
        self.component_api = component_api
        self.coordinator = coordinator
        self.lotto_type = lotto_type

        self.translation_key = TRANSLATION_KEY

        if self.lotto_type == LottoTypes.EURO_JACKPOT:
            self._name = "Euro jackpot"
            self._unique_id = "euro_jackpot"
        elif self.lotto_type == LottoTypes.VIKING_LOTTO:
            self._name = "Viking lotto"
            self._unique_id = "viking_lotto"
        else:
            self._name = "Lotto"
            self._unique_id = "lotto"

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
    def native_value(self) -> str | None:
        """Native value.

        Returns:
            str | None: Native value

        """
        match self.lotto_type:
            case LottoTypes.EURO_JACKPOT:
                return str(int(self.component_api.euro_jackpot_price_pool / 1000000))
            case LottoTypes.VIKING_LOTTO:
                return str(int(self.component_api.viking_lotto_price_pool / 1000000))
            case _:
                return str(int(self.component_api.lotto_price_pool / 1000000))

    # ------------------------------------------------------
    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit the value is expressed in."""

        return "mio"

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """
        attr: dict = {}

        if self.lotto_type == LottoTypes.EURO_JACKPOT:
            attr["price_pool"] = self.component_api.euro_jackpot_price_pool
        elif self.lotto_type == LottoTypes.VIKING_LOTTO:
            attr["price_pool"] = self.component_api.viking_lotto_price_pool
        else:
            attr["price_pool"] = self.component_api.lotto_price_pool
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


# ------------------------------------------------------
# ------------------------------------------------------
class LottoScrollSensor(ComponentEntity, SensorEntity):
    """Sensor class for lotto scroll."""

    # ------------------------------------------------------
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        component_api: ComponentApi,
    ) -> None:
        """Lotto scroll sensor."""
        super().__init__(coordinator, entry)

        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry
        self.component_api = component_api
        self.coordinator = coordinator
        self._name = "Lotto puljer"
        self._unique_id = "lotto_puljer"
        self.refresh_type: RefreshType = RefreshType.NORMAL

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
            self.coordinator.update_interval = timedelta(minutes=1)

        if self.refresh_type == RefreshType.LISTEN_TO_TIMER_TRIGGER:
            await self.coordinator.async_refresh()

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name.

        Returns:
            str: Name

        """
        return self._name

    # ------------------------------------------------------
    # @property
    # def icon(self) -> str:
    #     """Icon.

    #     Returns:
    #         str: Icon

    #     """
    #     return "mdi:cash-multiple"

    # ------------------------------------------------------
    @property
    def native_value(self) -> str | None:
        """Native value."""
        return self.component_api.lotto_price_pool_scroll

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """

        return {}

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

        self.async_on_remove(start.async_at_started(self.hass, self.async_hass_started))

    # ------------------------------------------------------
    async def async_hass_started(self, _event: Event) -> None:
        """Hass started."""

        if self.refresh_type == RefreshType.NORMAL:
            self.coordinator.update_interval = timedelta(minutes=1)
        elif self.refresh_type == RefreshType.LISTEN_TO_TIMER_TRIGGER:
            if not await self.timer_trigger.async_validate_timer():
                self.coordinator.update_interval = timedelta(minutes=1)
                self.refresh_type = RefreshType.NORMAL
