"""Config flow to configure the My dyn ip integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DOMAIN_NAME


class ComponentConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for My dyn ip."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        # if user_input is not None:
        return self.async_create_entry(title=DOMAIN_NAME, data={})
