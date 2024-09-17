"""Test the Hiper Drift component_api."""

from datetime import timedelta
import logging

from aiohttp.client import ClientSession
import pytest

from custom_components.hiper_drift import ComponentApi
from custom_components.hiper_drift.const import (
    CONF_CITY,
    CONF_CITY_CHECK,
    CONF_GENERAL_MSG,
    CONF_REGION,
    CONF_STREET,
    CONF_STREET_CHECK,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from tests.conftest import *  # noqa: F401, F403
from tests.conftest import MockConfigEntry  # noqa: F401, F403


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class TestComponentApi:
    """Test Hiper drift."""

    # ------------------------------------------------------------------
    @pytest.mark.parametrize("expected_lingering_timers", [True])
    @pytest.mark.parametrize("region", ["sj_bh", "fyn", "jylland"])
    async def test_hiper_check_update(self, hass: HomeAssistant, region: str) -> None:
        """Test check for hiper updates."""

        async def _async_update_data():
            #  raise ConfigEntryError("Incompatible firmware version")
            pass

        coordinator = DataUpdateCoordinator(
            hass,
            logging.getLogger(__name__),
            name="any",
            update_method=_async_update_data,
            update_interval=timedelta(seconds=1000),
        )

        conf_data: dict = {
            CONF_REGION: region,
            CONF_GENERAL_MSG: True,
            CONF_CITY_CHECK: True,
            CONF_CITY: "Hillerød",
            CONF_STREET_CHECK: True,
            CONF_STREET: "Skovledet",
        }

        entry = MockConfigEntry(
            domain="hiper_drift_test",
            data=conf_data,
            options=conf_data,
        )
        entry.add_to_hass(hass)

        try:
            self.sesion = ClientSession()
            comp: ComponentApi = ComponentApi(hass, coordinator, entry, self.sesion)
            await comp.async_check_hiper(region)
            await self.sesion.close()

            await hass.async_block_till_done(wait_background_tasks=True)

            assert True
        except Exception:  # noqa: BLE001
            pytest.fail("Hiper check failed")

    # ------------------------------------------------------------------
    @pytest.mark.parametrize("expected_lingering_timers", [True])
    @pytest.mark.parametrize("region", ["fail"])
    async def test_hiper_check_update_fail(
        self, hass: HomeAssistant, region: str
    ) -> None:
        """Test check for hiper updates fails."""

        async def _async_update_data():
            #  raise ConfigEntryError("Incompatible firmware version")
            pass

        coordinator = DataUpdateCoordinator(
            hass,
            logging.getLogger(__name__),
            name="any",
            update_method=_async_update_data,
            update_interval=timedelta(seconds=1000),
        )

        conf_data: dict = {
            CONF_REGION: region,
            CONF_GENERAL_MSG: True,
            CONF_CITY_CHECK: True,
            CONF_CITY: "Hillerød",
            CONF_STREET_CHECK: True,
            CONF_STREET: "Skovledet",
        }

        entry = MockConfigEntry(
            domain="hiper_drift_test",
            data=conf_data,
            options=conf_data,
        )
        entry.add_to_hass(hass)

        try:
            self.sesion = ClientSession()
            comp: ComponentApi = ComponentApi(hass, coordinator, entry, self.sesion)
            await comp.async_check_hiper(region)
            await self.sesion.close()

            await hass.async_block_till_done(wait_background_tasks=True)

            pytest.fail("Hiper check failed")
        except Exception:  # noqa: BLE001
            assert True
