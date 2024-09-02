"""Settings handling."""

from collections.abc import Callable
from typing import Any

import jsonpickle

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class StoreMigrate(Store):
    """When migration storage layout."""

    custom_migrate_func: Callable[[int, int, Any], Any] | None = None

    # ------------------------------------------------------------------
    async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        old_data: Any,
    ) -> Any:
        """Migrate to the new version."""

        if self.custom_migrate_func is not None:
            return await self.custom_migrate_func(
                old_major_version, old_minor_version, old_data
            )

        return old_data


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class StorageJson:
    """Settings class."""

    def __init__(
        self,
        hass: HomeAssistant,
        async_migrate_func: Callable[[int, int, Any], Any] | None = None,
    ) -> None:
        """Init."""

        self.write_hidden_attributes___: bool = False
        self.hass___ = hass
        self.store___ = StoreMigrate(self.hass___, STORAGE_VERSION, STORAGE_KEY)
        self.store___.custom_migrate_func = async_migrate_func

    # ------------------------------------------------------------------
    async def async_read_settings(self) -> None:
        """read_settings."""
        if hasattr(self, "__dict__") is False:
            return

        data = await self.store___.async_load()

        if data is None:
            return
        tmp_obj = self.decode_data(data)

        if hasattr(tmp_obj, "__dict__") is False:
            return

        self.__dict__.update(tmp_obj.__dict__)

    # ------------------------------------------------------------------
    def decode_data(self, data: Any):
        """Decode data."""
        return jsonpickle.decode(data)

    # ------------------------------------------------------------------
    async def async_write_settings(
        self,
    ) -> None:
        """Write settings."""

        jsonpickle.set_encoder_options("json", ensure_ascii=False)

        await self.store___.async_save(self.encode_data(self))

    # ------------------------------------------------------------------
    def encode_data(self, data: Any):
        """Encode data."""
        return jsonpickle.encode(data, unpicklable=True)

    # ------------------------------------------------------------------
    async def async_remove_settings(self) -> None:
        """Remove settings."""
        await self.store___.async_remove()

    # ------------------------------------------------------------------
    def __getstate__(self) -> dict:
        """Get state."""
        tmp_dict = self.__dict__.copy()
        del tmp_dict["write_hidden_attributes___"]
        del tmp_dict["hass___"]
        del tmp_dict["store___"]

        if self.write_hidden_attributes___ is False:
            try:

                def remove_hidden_attrib(obj) -> None:
                    for key in list(obj):
                        if len(key) > 2 and key[0:2] == "__":
                            continue
                        elif hasattr(obj[key], "__dict__"):  # noqa: RET507
                            remove_hidden_attrib(obj[key].__dict__)

                        # Remove hidden attributes
                        elif len(key) > 3 and key[-3:] == "___":
                            del obj[key]

                        elif isinstance(obj[key], list):
                            for item in obj[key]:
                                if hasattr(item, "__dict__"):
                                    remove_hidden_attrib(item.__dict__)

                remove_hidden_attrib(tmp_dict)
            except Exception:  # noqa: BLE001
                pass
        return tmp_dict
