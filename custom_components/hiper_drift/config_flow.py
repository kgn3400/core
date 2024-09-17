"""Config flow for Hiperdrift integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol

#  from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
)
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
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input."""

    if (
        user_input[CONF_GENERAL_MSG] is False
        and user_input[CONF_CITY_CHECK] is False
        and user_input[CONF_STREET_CHECK] is False
    ):
        raise SchemaFlowError("missing_selection")

    if CONF_CITY not in user_input:
        user_input[CONF_CITY] = ""

    if user_input[CONF_CITY_CHECK] and user_input[CONF_CITY].strip() == "":
        raise SchemaFlowError("missing_city")

    if CONF_STREET not in user_input:
        user_input[CONF_STREET] = ""

    if user_input[CONF_STREET_CHECK] and user_input[CONF_STREET].strip() == "":
        raise SchemaFlowError("missing_street")

    return user_input


CONFIG_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REGION, default=CONF_SJ_BH_REGION): SelectSelector(
            SelectSelectorConfig(
                options=[CONF_SJ_BH_REGION, CONF_FYN_REGION, CONF_JYL_REGION],
                sort=True,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=TRANSLATION_KEY_REGION,
            )
        ),
        vol.Required(
            CONF_GENERAL_MSG,
            default=True,
        ): cv.boolean,
        vol.Required(
            CONF_CITY_CHECK,
            default=False,
        ): cv.boolean,
        vol.Required(
            CONF_CITY,
        ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        vol.Required(
            CONF_STREET_CHECK,
            default=True,
        ): cv.boolean,
        vol.Optional(
            CONF_STREET,
        ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
    }
)

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        CONFIG_OPTIONS_SCHEMA,
        validate_user_input=_validate_input,
    ),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(
        CONFIG_OPTIONS_SCHEMA,
        validate_user_input=_validate_input,
    ),
}


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""

        return cast(str, DOMAIN_NAME)
