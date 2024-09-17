"""Test the pypi_updates component_api."""

from aiohttp.client import ClientSession
import pytest

from custom_components.pypi_updates.component_api import (
    FindPyPiPackage,
    NotFoundException,
)
from homeassistant.core import HomeAssistant
from tests.conftest import *  # noqa: F401, F403
from tests.conftest import MockConfigEntry  # noqa: F401, F403


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class TestComponentApi:
    """Test pypi_updates."""

    # ------------------------------------------------------------------
    @pytest.mark.parametrize("expected_lingering_timers", [True])
    @pytest.mark.parametrize("package", ["ruff", "uv"])
    async def test_package_exists(self, hass, package: str) -> None:
        """Test check package exists."""

        try:
            self.sesion = ClientSession()
            comp: FindPyPiPackage = FindPyPiPackage()
            assert await comp.async_get_package_version(self.sesion, package) != ""
            await self.sesion.close()
            await hass.async_block_till_done(wait_background_tasks=True)

        except Exception:  # noqa: BLE001
            pytest.fail("Pypi updates failed")

    # ------------------------------------------------------------------
    @pytest.mark.parametrize("expected_lingering_timers", [True])
    @pytest.mark.parametrize("package", ["fail_package"])
    async def test_package_exists_fail(self, hass: HomeAssistant, package: str) -> None:
        """Test check package exists."""

        try:
            self.sesion = ClientSession()
            comp: FindPyPiPackage = FindPyPiPackage()
            assert await comp.async_get_package_version(self.sesion, package) == ""
            await self.sesion.close()
            await hass.async_block_till_done(wait_background_tasks=True)

        except NotFoundException:  # noqa: BLE001
            assert True
        except Exception:  # noqa: BLE001
            pytest.fail("Pypi updates failed")
