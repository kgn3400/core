"""Config flow for Lotto DK integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol

from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
)

from .const import (
    CONF_EURO_JACKPOT,
    CONF_LISTEN_TO_TIMER_TRIGGER,
    CONF_LOTTO,
    CONF_RESTART_TIMER,
    CONF_VIKING_LOTTO,
    DOMAIN,
    DOMAIN_NAME,
)


# ------------------------------------------------------------------
async def _validate_input(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input."""

    if (
        user_input[CONF_EURO_JACKPOT] is False
        and user_input[CONF_LOTTO] is False
        and user_input[CONF_VIKING_LOTTO] is False
    ):
        raise SchemaFlowError("missing_selection")
    return user_input


CONFIG_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_EURO_JACKPOT,
            default=True,
        ): cv.boolean,
        vol.Required(
            CONF_LOTTO,
            default=True,
        ): cv.boolean,
        vol.Required(
            CONF_VIKING_LOTTO,
            default=True,
        ): cv.boolean,
        vol.Optional(
            CONF_LISTEN_TO_TIMER_TRIGGER,
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(integration="timer", multiple=False),
        ),
        vol.Optional(
            CONF_RESTART_TIMER,
            default=False,
        ): cv.boolean,
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
