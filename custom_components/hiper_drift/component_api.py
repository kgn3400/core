"""Component api for Hiper drift."""

from asyncio import timeout
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re
from typing import Any

from aiohttp.client import ClientSession
from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CITY,
    CONF_CITY_CHECK,
    CONF_CONTENT,
    CONF_FYN_REGION,
    CONF_GENERAL_MSG,
    CONF_IS_ON,
    CONF_JYL_REGION,
    CONF_MSG,
    CONF_REGION,
    CONF_SJ_BH_REGION,
    CONF_STREET,
    CONF_STREET_CHECK,
    DOMAIN,
)


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class ComponentApi:
    """Hiper interface."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        session: ClientSession | None,
    ) -> None:
        """Hiper api."""

        self.hass: HomeAssistant = hass
        self.coordinator: DataUpdateCoordinator = coordinator
        self.entry: ConfigEntry = entry
        self.session: ClientSession | None = session

        self.region: str = entry.options[CONF_REGION]
        self.general_msg: bool = entry.options[CONF_GENERAL_MSG]
        self.city_check: bool = entry.options[CONF_CITY_CHECK]
        self.city: str = entry.options[CONF_CITY]
        self.street_check: bool = entry.options[CONF_STREET_CHECK]
        self.street: str = entry.options[CONF_STREET]

        self.request_timeout: int = 10
        self.close_session: bool = False
        self.is_on: bool = self.entry.options.get(CONF_IS_ON, False)
        self.msg: str = self.entry.options.get(CONF_MSG, "")
        self.content: str = self.entry.options.get(CONF_CONTENT, "")
        self.last_updated: datetime = None
        self.supress_update_listener: bool = False

        self.coordinator.update_interval = timedelta(minutes=15)
        self.coordinator.update_method = self.async_update

        """Setup the actions for the Hiper integration."""
        hass.services.async_register(DOMAIN, "update", self.async_update_service)
        hass.services.async_register(DOMAIN, "reset", self.async_reset_service)

    # ------------------------------------------------------------------
    async def async_reset_service(self, call: ServiceCall) -> None:
        """Hiper service interface."""
        self.is_on = False
        await self.update_config()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_update_service(self, call: ServiceCall) -> None:
        """Hiper service interface."""
        self.msg = ""
        self.content = ""
        await self.update_config()

        await self.async_update()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_update(self) -> None:
        """Hiper interface."""

        if self.session is None:
            self.session = ClientSession()
            self.close_session = True

        await self.async_check_hiper(self.region)

        if self.session and self.close_session:
            await self.session.close()

    # ------------------------------------------------------
    async def async_check_hiper(self, region: str) -> None:
        """Check if Hiper drift."""
        tmp_msg: str = ""
        tmp_content: str = ""
        is_updated: bool = False
        ROOT_DRIFT_URL: str = "https://www.hiper.dk/drift/"

        try:
            async with timeout(self.request_timeout):
                response = await self.session.get(ROOT_DRIFT_URL)

                soup = await self.hass.async_add_executor_job(
                    BeautifulSoup, await response.text(), "lxml"
                )

            if (
                self.general_msg
                and soup.find(string=re.compile("generelle driftssager", re.IGNORECASE))
                is not None
                and soup.find(
                    string=re.compile("ingen generelle driftssager", re.IGNORECASE)
                )
                is None
            ):
                tmp_msg = "Generelle driftsager"

                tag = soup.select(
                    "body > div.site-wrap > main > div.service-status-wrapper > section > div:nth-child(1) > ul > li > div > div.details"
                )[0]
                tmp_content = tag.text.strip()
                is_updated = True

            if region == CONF_SJ_BH_REGION:
                url_region: str = ROOT_DRIFT_URL + "region/sjaelland-og-bornholm"
            elif region == CONF_FYN_REGION:
                url_region = ROOT_DRIFT_URL + "region/fyn"

            elif region == CONF_JYL_REGION:
                url_region = ROOT_DRIFT_URL + "region/jylland"

            else:
                ROOT_DRIFT_URL = "https://www.fail.xx"

            async with timeout(self.request_timeout):
                response = await self.session.get(url_region)

                soup = await self.hass.async_add_executor_job(
                    BeautifulSoup, await response.text(), "lxml"
                )

            if response.real_url.path.upper().find("/region/".upper()) == -1:
                if (
                    self.city_check
                    and (
                        xx := soup.find(
                            string=re.compile(
                                " " + self.city.strip() + " ", re.IGNORECASE
                            )
                        )
                    )
                    is not None
                ):
                    tmp_msg = "Lok" + f"ale driftssager for {self.city.strip()}"
                    tmp_content = xx.strip()
                    is_updated = True

                if (
                    self.street_check
                    and soup.find(
                        string=re.compile(" " + self.city.strip() + " ", re.IGNORECASE)
                    )
                    is not None
                    and (
                        xx := soup.find(
                            string=re.compile(" " + self.street.strip(), re.IGNORECASE)
                        )
                    )
                    is not None
                ):
                    tmp_msg = (
                        "Lok"
                        f"ale driftssager for {self.city.strip()} på {self.street}"
                    )
                    tmp_content = xx.strip()
                    is_updated = True

            if is_updated:
                if tmp_msg != self.msg or tmp_content != self.content:
                    self.msg = tmp_msg
                    self.content = tmp_content
                    self.is_on = True
                    self.last_updated = datetime.now(UTC)
                    await self.update_config()
            else:
                if self.is_on:
                    await self.update_config()

                self.msg = ""
                self.content = ""
                self.is_on = False
                self.last_updated = None

        except TimeoutError:
            pass

    # ------------------------------------------------------------------
    async def update_config(self) -> None:
        """Update config."""

        tmp_options: dict[str, Any] = self.entry.options.copy()
        tmp_options[CONF_MSG] = self.msg
        tmp_options[CONF_CONTENT] = self.content
        tmp_options[CONF_IS_ON] = self.is_on
        self.supress_update_listener = True

        self.hass.config_entries.async_update_entry(
            self.entry, data=tmp_options, options=tmp_options
        )
