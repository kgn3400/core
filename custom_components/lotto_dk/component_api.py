"""Lotto interface."""

from asyncio import timeout
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from aiohttp.client import ClientSession
from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN


class LottoTypes(Enum):
    """Lotto enum."""

    LOTTO = 1
    EURO_JACKPOT = 2
    VIKING_LOTTO = 3


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class ComponentApi:
    """Lotto interface."""

    _EURO_JACKPOT_URL = "https://danskespil.dk/eurojackpot"
    _LOTTO_URL = "https://danskespil.dk/lotto"
    _VIKING_LOTTO_URL = "https://danskespil.dk/vikinglotto"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        session: ClientSession | None,
        euro_jackpot: bool,
        lotto: bool,
        viking_lotto: bool,
    ) -> None:
        """Lotto interface."""
        self.hass = hass
        self.coordinator: DataUpdateCoordinator = coordinator
        self.session: ClientSession = session
        self.get_euro_jackpot: bool = euro_jackpot
        self.euro_jackpot_price_pool: int = 0
        self.get_lotto: bool = lotto
        self.lotto_price_pool: int = 0
        self.get_viking_lotto: bool = viking_lotto
        self.viking_lotto_price_pool: int = 0
        self.request_timeout: float = 3
        self.close_session: bool = False
        self.lotto_price_pool_scroll: str = ""
        self.lotto_price_pool_scroll_next: LottoTypes = LottoTypes.EURO_JACKPOT
        self.next_webscrape: datetime = datetime.now()
        self.next_webscrape_delta: int = 60

        self.coordinator.update_interval = timedelta(minutes=10)
        self.coordinator.update_method = self.async_update
        """Setup the actions for the Lotto integration."""
        hass.services.async_register(DOMAIN, "update", self.async_update_service)

        self.find_next_lotto_scroll()

    # ------------------------------------------------------------------
    async def async_update_service(self, call: ServiceCall) -> None:
        """Lotto update service interface."""
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_update(self) -> None:
        """Lotto update interface."""

        if self.next_webscrape < datetime.now():
            self.next_webscrape = datetime.now() + timedelta(
                minutes=self.next_webscrape_delta
            )

            if self.session is None:
                self.session = ClientSession()
                self.close_session = True

            if self.get_lotto:
                pool: int = await self._async_get_price_pool(self._LOTTO_URL)

                if pool != 0:
                    self.lotto_price_pool = pool

            if self.get_viking_lotto:
                pool: int = await self._async_get_price_pool(self._VIKING_LOTTO_URL)

                if pool != 0:
                    self.viking_lotto_price_pool = pool

            if self.get_euro_jackpot:
                pool: int = await self._async_get_price_pool(self._EURO_JACKPOT_URL)

                if pool != 0:
                    self.euro_jackpot_price_pool = pool

            if self.session and self.close_session:
                await self.session.close()

        self.roll_price_pools()

    # ------------------------------------------------------
    async def _async_get_price_pool(self, url: str) -> int:
        try:
            async with timeout(self.request_timeout):
                response = await self.session.request("GET", url)
                soup = await self.hass.async_add_executor_job(
                    BeautifulSoup, await response.text(), "lxml"
                )
                return int(soup.title.text.split()[4].replace(".", ""))
        except TimeoutError:
            pass
        except IndexError:
            pass

        return 0

    # ------------------------------------------------------
    def roll_price_pools(self) -> None:
        """Roll price pools."""

        if (
            self.get_euro_jackpot
            and self.lotto_price_pool_scroll_next == LottoTypes.EURO_JACKPOT
        ):
            self.lotto_price_pool_scroll = (
                "Euro jackpot: "
                + str(int(self.euro_jackpot_price_pool / 1000000))
                + " mio"
            )
        elif self.get_lotto and self.lotto_price_pool_scroll_next == LottoTypes.LOTTO:
            self.lotto_price_pool_scroll = (
                "Lotto: " + str(int(self.lotto_price_pool / 1000000)) + " mio"
            )
        elif (
            self.get_viking_lotto
            and self.lotto_price_pool_scroll_next == LottoTypes.VIKING_LOTTO
        ):
            self.lotto_price_pool_scroll = (
                "Viking lotto: "
                + str(int(self.viking_lotto_price_pool / 1000000))
                + " mio"
            )

        self.find_next_lotto_scroll()

    # ------------------------------------------------------
    def find_next_lotto_scroll(self) -> None:
        """Roll price pools."""

        if self.lotto_price_pool_scroll_next == LottoTypes.EURO_JACKPOT:
            if self.get_lotto:
                self.lotto_price_pool_scroll_next = LottoTypes.LOTTO
            elif self.get_viking_lotto:
                self.lotto_price_pool_scroll_next = LottoTypes.VIKING_LOTTO
            return

        if self.lotto_price_pool_scroll_next == LottoTypes.LOTTO:
            if self.get_viking_lotto:
                self.lotto_price_pool_scroll_next = LottoTypes.VIKING_LOTTO
            elif self.get_euro_jackpot:
                self.lotto_price_pool_scroll_next = LottoTypes.EURO_JACKPOT
            return

        if self.lotto_price_pool_scroll_next == LottoTypes.VIKING_LOTTO:
            if self.get_euro_jackpot:
                self.lotto_price_pool_scroll_next = LottoTypes.EURO_JACKPOT
            elif self.get_lotto:
                self.lotto_price_pool_scroll_next = LottoTypes.LOTTO
            return
