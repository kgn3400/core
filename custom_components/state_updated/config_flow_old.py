"""Config flow for State updated integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN

#  from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_ATTRIBUTE,
    CONF_DEVICE_ID,
    CONF_ENTITY_ID,
    CONF_ICON,
    CONF_NAME,
    __short_version__,
)
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.selector import (
    IconSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TemplateSelector,
)

from .const import (
    CONF_CLEAR_UPDATES_AFTER_HOURS,
    CONF_DEFAULT_TEXT_TEMPLATE,
    CONF_LAST_UPDATED,
    CONF_NEW_VALUE,
    CONF_OLD_VALUE,
    CONF_TEXT_TEMPLATE,
    CONF_UPDATED,
    DOMAIN,
    LOGGER,
)
from .translate import Translate


# ------------------------------------------------------------------
async def _validate_input(
    hass: HomeAssistant, user_input: dict[str, Any], errors: dict[str, str]
) -> bool:
    """Validate the user input allows us to connect."""

    return True


# ------------------------------------------------------------------
async def _create_form(
    hass: HomeAssistant, user_input: dict[str, Any] | None = None, step: str = ""
) -> vol.Schema:
    """Create a form for step/option."""

    if user_input is None:
        user_input = {}

    match step:
        case "user_extra" | "init":
            if __short_version__ >= "2024.7":
                return vol.Schema(
                    {
                        vol.Optional(
                            CONF_ATTRIBUTE,
                            default=user_input.get(CONF_ATTRIBUTE, ""),
                        ): selector.AttributeSelector(
                            selector.AttributeSelectorConfig(
                                entity_id=user_input[CONF_ENTITY_ID]
                            )
                        ),
                        vol.Optional(
                            CONF_ICON,
                            default=user_input.get(CONF_ICON, ""),
                        ): IconSelector(),
                        vol.Optional(
                            CONF_DEVICE_ID,
                            default=user_input.get(CONF_DEVICE_ID, ""),
                        ): selector.DeviceSelector(),
                        vol.Required(
                            CONF_CLEAR_UPDATES_AFTER_HOURS,
                            default=user_input.get(CONF_CLEAR_UPDATES_AFTER_HOURS, 24),
                        ): NumberSelector(
                            NumberSelectorConfig(
                                min=0.1,
                                max=999,
                                step="any",
                                mode=NumberSelectorMode.BOX,
                                unit_of_measurement="hours",
                            )
                        ),
                        vol.Optional(
                            CONF_TEXT_TEMPLATE,
                            default=user_input.get(
                                CONF_TEXT_TEMPLATE,
                                await Translate(hass).async_get_localized_str(
                                    CONF_DEFAULT_TEXT_TEMPLATE,
                                    load_only=CONF_DEFAULT_TEXT_TEMPLATE,
                                ),
                            ),
                        ): TemplateSelector(),
                    },
                )
            return vol.Schema(
                {
                    vol.Optional(
                        CONF_ATTRIBUTE,
                        default=user_input.get(CONF_ATTRIBUTE, ""),
                    ): selector.AttributeSelector(
                        selector.AttributeSelectorConfig(
                            entity_id=user_input[CONF_ENTITY_ID]
                        )
                    ),
                    vol.Optional(
                        CONF_ICON,
                        default=user_input.get(CONF_ICON, ""),
                    ): IconSelector(),
                    vol.Required(
                        CONF_CLEAR_UPDATES_AFTER_HOURS,
                        default=user_input.get(CONF_CLEAR_UPDATES_AFTER_HOURS, 24),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0.1,
                            max=999,
                            step="any",
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="hours",
                        )
                    ),
                    vol.Optional(
                        CONF_TEXT_TEMPLATE,
                        default=user_input.get(
                            CONF_TEXT_TEMPLATE,
                            await Translate(hass).async_get_localized_str(
                                CONF_DEFAULT_TEXT_TEMPLATE,
                                load_only=CONF_DEFAULT_TEXT_TEMPLATE,
                            ),
                        ),
                    ): TemplateSelector(),
                }
            )

        case "user" | _:
            return vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME,
                        default=user_input.get(CONF_NAME, ""),
                    ): selector.TextSelector(),
                    vol.Required(
                        CONF_ENTITY_ID,
                        default=user_input.get(CONF_ENTITY_ID),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=SENSOR_DOMAIN, multiple=False
                        ),
                    ),
                }
            )


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    tmp_user_input: dict[str, Any] | None

    # ------------------------------------------------------------------
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                if await _validate_input(self.hass, user_input, errors):
                    self.tmp_user_input = user_input

                    return self.async_show_form(
                        step_id="user_extra",
                        data_schema=await _create_form(
                            self.hass, user_input, "user_extra"
                        ),
                        errors=errors,
                    )

            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        # else:
        #     user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=await _create_form(self.hass, user_input, "user"),
            errors=errors,
            last_step=False,
        )

    # ------------------------------------------------------------------
    async def async_step_user_extra(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        user_input |= self.tmp_user_input

        if user_input is not None:
            try:
                if await _validate_input(self.hass, user_input, errors):
                    if CONF_NAME in user_input:
                        title: str = user_input[CONF_NAME]
                    else:
                        title = user_input[CONF_ENTITY_ID]
                        title = title[title.find(".") + 1 :] + " updated"
                        title = title.replace("_", " ")

                    if (
                        CONF_ATTRIBUTE in user_input
                        and str(user_input.get(CONF_ATTRIBUTE, "")).strip() == ""
                    ):
                        del user_input[CONF_ATTRIBUTE]

                    user_input[CONF_NEW_VALUE] = user_input[
                        CONF_OLD_VALUE
                    ] = await self.await_get_current_state(user_input)

                    user_input[CONF_UPDATED] = False
                    user_input[CONF_LAST_UPDATED] = datetime.now(UTC).isoformat()

                    return self.async_create_entry(
                        title=title,
                        data=user_input,
                        options=user_input,
                    )

            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        # else:
        #     user_input = {}

        return self.async_show_form(
            step_id="user_extra",
            data_schema=await _create_form(self.hass, user_input, "user_extra"),
            errors=errors,
            last_step=True,
        )

    # ------------------------------------------------------------------
    async def await_get_current_state(self, user_input: dict[str, Any]) -> Any:
        """Get current state."""
        tmp_state: Any = ""
        state: State | None = self.hass.states.get(user_input[CONF_ENTITY_ID])

        if state is not None:
            if CONF_ATTRIBUTE in user_input:
                tmp_state = state.attributes.get(user_input[CONF_ATTRIBUTE])
            else:
                tmp_state = state.state

        return tmp_state

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
    """Options flow for State updated."""

    def __init__(
        self,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize options flow."""

        self.config_entry = config_entry

    # ------------------------------------------------------------------
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                if await _validate_input(self.hass, user_input, errors):
                    tmp_input = self.config_entry.options.copy() | user_input

                    if (
                        CONF_ATTRIBUTE in tmp_input
                        and str(tmp_input.get(CONF_ATTRIBUTE, "")).strip() == ""
                    ):
                        del tmp_input[CONF_ATTRIBUTE]

                    return self.async_create_entry(
                        data=tmp_input,
                    )
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="init",
            data_schema=await _create_form(
                self.hass, self.config_entry.options.copy(), "init"
            ),
            errors=errors,
            last_step=True,
        )
