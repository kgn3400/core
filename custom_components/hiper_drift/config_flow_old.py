"""Config flow for Hiperdrift integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

#  from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_CITY,
    CONF_CITY_CHECK,
    CONF_FYN_REGION,
    CONF_GENERAL_MSG,
    CONF_JYL_REGION,
    CONF_REGION,
    CONF_SJ_BH_REGION,
    CONF_STREET,
    CONF_STREET_CHECK,
    DOMAIN,
    DOMAIN_NAME,
    TRANSLATION_KEY_REGION,
)


# ------------------------------------------------------------------
async def _validate_input(
    hass: HomeAssistant, user_input: dict[str, Any], errors: dict[str, str]
) -> bool:
    """Validate the user input."""

    if (
        user_input[CONF_GENERAL_MSG] is False
        and user_input[CONF_CITY_CHECK] is False
        and user_input[CONF_STREET_CHECK] is False
    ):
        errors["base"] = "missing_selection"
        return False

    if CONF_CITY not in user_input:
        user_input[CONF_CITY] = ""

    if user_input[CONF_CITY_CHECK] is True and user_input[CONF_CITY].strip() == "":
        errors[CONF_CITY] = "missing_city"
        return False
        # raise MissingCity

    if CONF_STREET not in user_input:
        user_input[CONF_STREET] = ""

    if user_input[CONF_STREET_CHECK] is True and user_input[CONF_STREET].strip() == "":
        errors[CONF_STREET] = "missing_street"
        return False

    # Return info that you want to store in the config entry.
    return True


# ------------------------------------------------------------------
def _create_form(
    user_input: dict[str, Any] | None = None,
) -> vol.Schema:
    """Create a form for step/option."""

    if user_input is None:
        user_input = {}

    return vol.Schema(
        {
            vol.Required(CONF_REGION, default=CONF_SJ_BH_REGION): SelectSelector(
                SelectSelectorConfig(
                    options=[CONF_SJ_BH_REGION, CONF_FYN_REGION, CONF_JYL_REGION],
                    sort=True,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key=TRANSLATION_KEY_REGION,
                )
            ),
            # vol.Required(
            #     CONF_REGION,
            #     default=user_input.get(CONF_REGION, "Sjælland og Bonholm"),
            # ): selector(
            #     {
            #         "select": {
            #             "options": [CONF_SJ_BH, CONF_FYN, CONF_JYL],
            #         }
            #     }
            # ),
            vol.Required(
                CONF_GENERAL_MSG,
                default=user_input.get(CONF_GENERAL_MSG, True),
            ): cv.boolean,
            vol.Required(
                CONF_GENERAL_MSG,
                default=user_input.get(CONF_GENERAL_MSG, True),
            ): cv.boolean,
            vol.Required(
                CONF_CITY_CHECK,
                default=user_input.get(CONF_CITY_CHECK, True),
            ): cv.boolean,
            vol.Optional(
                CONF_CITY,
                description={"suggested_value": user_input.get(CONF_CITY, "")},
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(
                CONF_STREET_CHECK,
                default=user_input.get(CONF_STREET_CHECK, True),
            ): cv.boolean,
            vol.Optional(
                CONF_STREET,
                description={"suggested_value": user_input.get(CONF_STREET, "")},
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        }
    )


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HiperDrift."""

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
            if await _validate_input(self.hass, user_input, errors):
                return self.async_create_entry(
                    title=DOMAIN_NAME, data=user_input, options=user_input
                )

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
    """Options flow for HiperDrift."""

    def __init__(
        self,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize options flow."""

        self.config_entry = config_entry

        self._selection: dict[str, Any] = {}
        self._configs: dict[str, Any] = self.config_entry.data.copy()
        self._options: dict[str, Any] = self.config_entry.options.copy()

    # ------------------------------------------------------------------
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if await _validate_input(self.hass, user_input, errors):
                return self.async_create_entry(title=DOMAIN_NAME, data=user_input)
        else:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id="init",
            data_schema=_create_form(user_input),
            errors=errors,
        )
