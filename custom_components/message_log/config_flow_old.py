"""Config flow for Pypi updates integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    BooleanSelector,
    IconSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_DEFAULT_ICON,
    CONF_LISTEN_TO_TIMER_TRIGGER,
    CONF_MARKDOWN_MESSAGE_LIST_COUNT,
    CONF_ORDER_BY_MESSAGE_LEVEL,
    CONF_REMOVE_MESSAGE_AFTER_HOURS,
    CONF_RESTART_TIMER,
    CONF_SCROLL_MESSAGES_EVERY_MINUTES,
    CONF_SCROLL_THROUGH_LAST_MESSAGES_COUNT,
    DOMAIN,
    DOMAIN_NAME,
    LOGGER,
)

#  from homeassistant import config_entries
from .fix_entity_selector import EntitySelector, EntitySelectorConfig


# ------------------------------------------------------------------
async def _validate_input(
    hass: HomeAssistant, user_input: dict[str, Any], errors: dict[str, str]
) -> bool:
    """Validate the user input."""

    #      errors["base"] = "missing_pypi_package"

    return True


# ------------------------------------------------------------------
def _create_form(
    user_input: dict[str, Any],
) -> vol.Schema:
    """Create a form for step/option."""

    return vol.Schema(
        {
            vol.Required(
                CONF_REMOVE_MESSAGE_AFTER_HOURS,
                default=user_input.get(CONF_REMOVE_MESSAGE_AFTER_HOURS, 24),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=696,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="hours",
                )
            ),
            vol.Required(
                CONF_SCROLL_MESSAGES_EVERY_MINUTES,
                default=user_input.get(CONF_SCROLL_MESSAGES_EVERY_MINUTES, 0.5),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0.5,
                    max=696,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="minutes",
                )
            ),
            vol.Optional(
                CONF_LISTEN_TO_TIMER_TRIGGER,
                default=user_input.get(CONF_LISTEN_TO_TIMER_TRIGGER, ""),
            ): EntitySelector(
                EntitySelectorConfig(integration="timer", multiple=False),
            ),
            vol.Optional(
                CONF_RESTART_TIMER,
                default=user_input.get(CONF_RESTART_TIMER, False),
            ): BooleanSelector(),
            vol.Required(
                CONF_SCROLL_THROUGH_LAST_MESSAGES_COUNT,
                default=user_input.get(CONF_SCROLL_THROUGH_LAST_MESSAGES_COUNT, 5),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=696,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="count",
                )
            ),
            vol.Required(
                CONF_MARKDOWN_MESSAGE_LIST_COUNT,
                default=user_input.get(CONF_MARKDOWN_MESSAGE_LIST_COUNT, 10),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=2,
                    max=100,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="count",
                )
            ),
            vol.Required(
                CONF_DEFAULT_ICON,
                default=user_input.get(CONF_DEFAULT_ICON, "mdi:message-badge-outline"),
            ): IconSelector(),
            vol.Required(
                CONF_ORDER_BY_MESSAGE_LEVEL,
                default=user_input.get(CONF_ORDER_BY_MESSAGE_LEVEL, True),
            ): cv.boolean,
        }
    )


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pypi updates."""

    VERSION = 1

    # ------------------------------------------------------------------
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            try:
                if await _validate_input(self.hass, user_input, errors):
                    return self.async_create_entry(
                        title=DOMAIN_NAME, data=user_input, options=user_input
                    )

            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        else:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=_create_form(user_input),
            errors=errors,
        )

    # ------------------------------------------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class OptionsFlowHandler(OptionsFlow):
    """Options flow for Pypi updates."""

    def __init__(
        self,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize options flow."""

        self.config_entry = config_entry

        # self._selection: dict[str, Any] = {}
        # self._configs: dict[str, Any] = self.config_entry.data.copy()
        self._options: dict[str, Any] = self.config_entry.options.copy()

    # ------------------------------------------------------------------
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                if await _validate_input(self.hass, user_input, errors):
                    return self.async_create_entry(title=DOMAIN_NAME, data=user_input)
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        else:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id="init",
            data_schema=_create_form(user_input),
            errors=errors,
        )
