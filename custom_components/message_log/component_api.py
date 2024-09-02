"""Component api."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import partial

from babel.dates import format_timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_MARKDOWN_MESSAGE_LIST_COUNT,
    CONF_ORDER_BY_MESSAGE_LEVEL,
    CONF_REMOVE_MESSAGE_AFTER_HOURS,
    CONF_SCROLL_THROUGH_LAST_MESSAGES_COUNT,
    DOMAIN,
    TRANSLATE_EXTRA,
)
from .message_log_settings import (
    MessageItem,
    MessageLevel,
    MessageListOrderBy,
    MessageListShow,
    MessageLogSettings,
)
from .translate import Translate


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class Translations:
    """Translations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Init."""

        self.now_str: str
        self.for_str: str

        self.ago_str: str

        self.message_str: str
        self.messages_str: str

        self.last_message_str: str

        self.received_str: str
        self.relevance_str: str

        self.all_str: str
        self.info_str: str
        self.attention_str: str
        self.warning_str: str
        self.error_str: str

        self.translate: Translate = Translate(hass, TRANSLATE_EXTRA)

    # ------------------------------------------------------------------
    async def async_refresh(self):
        """Refresh."""
        self.now_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".rt_now",
        )

        self.for_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".rt_for",
        )

        self.ago_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".rt_ago",
        )

        self.message_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".message",
        )
        self.messages_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".message",
        )
        self.messages_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".messages",
        )
        self.last_message_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".last_message",
        )

        self.received_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".received",
        )
        self.relevance_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".relevance",
        )
        self.all_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".all",
        )
        self.info_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".info",
        )
        self.attention_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".attention",
        )
        self.warning_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".warning",
        )
        self.error_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".error",
        )


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class ComponentApi:
    """Message log interface."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Component api."""
        self.hass = hass
        self.entry: ConfigEntry = entry

        self.coordinator: DataUpdateCoordinator
        self.scroll_message_pos: int = -1
        self.markdown: str = ""
        self.markdown_message_list: str = ""
        self.markdown_message_settings: str = ""
        self.message_list_sorted: list[MessageItem] = []

        self.settings: MessageLogSettings = MessageLogSettings(
            hass, self.entry.options.get(CONF_ORDER_BY_MESSAGE_LEVEL, True)
        )

        self.translate: Translate = Translate(hass, TRANSLATE_EXTRA)
        self.translations: Translations = Translations(hass)

        """Set up the actions for the Message log integration."""
        hass.services.async_register(
            DOMAIN,
            "add",
            self.async_add_message_service,
        )
        hass.services.async_register(
            DOMAIN,
            "remove",
            self.async_remove_messages_service,
        )
        hass.services.async_register(
            DOMAIN,
            "orderby",
            self.async_messagelist_orderby_service,
        )
        hass.services.async_register(
            DOMAIN,
            "show",
            self.async_messagelist_show_service,
        )

    # ------------------------------------------------------------------
    async def async_relative_time_received(self, date_time: datetime) -> str:
        """Relative time received."""

        return (
            self.translations.received_str
            + " "
            + await self.async_relative_time(date_time)
        )

    # ------------------------------------------------------------------
    async def async_relative_time(self, date_time: datetime) -> str:
        """Relative time."""

        now = datetime.now(UTC)
        diff: timedelta = date_time - now
        # diff: timedelta = now - date_time

        diff_str: str = await self.hass.async_add_executor_job(
            partial(
                format_timedelta,
                delta=diff,
                add_direction=True,
                locale=self.translate.acive_language,
            )
        )
        return diff_str

    # ------------------------------------------------------------------
    async def async_remove_messages_service(self, call: ServiceCall) -> None:
        """Remove nessage service."""
        if "message_level" in call.data:
            tmp_message_level: MessageLevel = MessageLevel[
                call.data.get("message_level", "INFO").upper()
            ]

            for index, item in reversed(list(enumerate(self.settings.message_list))):
                if item.message_level == tmp_message_level:
                    del self.settings.message_list[index]
        else:
            self.settings.message_list.clear()

        self.settings.set_highest_message_level()
        await self.settings.async_write_settings()
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_add_message_service(self, call: ServiceCall) -> None:
        """Message log add service."""

        tmp_dict = call.data.copy()

        if "remove_after" not in tmp_dict:
            tmp_dict["remove_after"] = self.entry.options.get(
                CONF_REMOVE_MESSAGE_AFTER_HOURS, 24
            )

        if "added_at" in tmp_dict:
            tmp_dict["added_at"] = datetime.strptime(
                tmp_dict["added_at"],
                # 2023-04-13 22:00:00
                "%Y-%m-%d %H:%M:%S",
            ).astimezone(UTC)

            # Hvorfor er denne bid kun nødvendig i udviklings miløet ??
            # timezonex = pytz.timezone(self.hass.config.time_zone)
            # tmp_off = timezonex.localize(tmp_dict["added_at"]).utcoffset()
            # tmp_dict["added_at"] -= timedelta(seconds=tmp_off.total_seconds())

        self.settings.message_list.insert(0, MessageItem(**tmp_dict))
        self.settings.set_highest_message_level()
        await self.settings.async_write_settings()
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_messagelist_orderby_service(self, call: ServiceCall) -> None:
        """Message list orderby."""

        if call.data.get("orderby") is None:
            self.settings.message_list_orderby = MessageListOrderBy(
                self.settings.message_list_orderby.succ(True)
            )
        else:
            self.settings.message_list_orderby = MessageListOrderBy[
                call.data.get("orderby", "MESSAGE_LEVEL").upper()
            ]

            if len(self.settings.message_list) > 1:
                self.scroll_message_pos = -1

        await self.settings.async_write_settings()
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_messagelist_show_service(self, call: ServiceCall) -> None:
        """Message list show."""

        if call.data.get("show") is None:
            self.settings.message_list_show = MessageListShow(
                self.settings.message_list_show.succ(True)
            )
        else:
            self.settings.message_list_orderby = MessageListOrderBy[
                call.data.get("show", "ALL").upper()
            ]

        await self.settings.async_write_settings()
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_update(self) -> None:
        """Message log Update."""

        await self.translations.async_refresh()
        await self.async_remove_outdated()
        # self.update_scroll_message_pos()
        await self.async_update_markdown()

    # ------------------------------------------------------------------
    async def async_remove_outdated(self) -> None:
        """Remove outdated."""
        save_settings: bool = False

        for index, item in reversed(list(enumerate(self.settings.message_list))):
            if item.remove_after < datetime.now(UTC):
                save_settings = True
                del self.settings.message_list[index]

        if save_settings:
            self.settings.set_highest_message_level()
            await self.settings.async_write_settings()

    # ------------------------------------------------------------------
    async def async_update_markdown(self) -> None:
        """Update markdown."""
        self.create_sorted_message_list(self.settings.message_list_orderby)
        await self.async_create_markdown_latest_and_scroll()

        self.create_sorted_message_list(
            self.settings.message_list_orderby, self.settings.message_list_show
        )
        await self.async_create_markdown_message_list()
        await self.async_create_markdown_message_settings()

        self.message_list_sorted.clear()

    # ------------------------------------------------------------------
    async def async_create_markdown_latest_and_scroll(self) -> None:
        """Markdown latest and scroll."""
        # Latest message
        if len(self.settings.message_list) > 0:
            item: MessageItem = self.settings.message_list[0]

            self.markdown = (
                f'## <font color={self.settings.highest_message_level_color}>  <ha-icon icon="mdi:message-outline"></ha-icon></font> { self.translations.message_str}\n'
                f'-  <font color={item.message_level_color}>  <ha-icon icon="{item.icon}"></ha-icon></font> <font size=3>{self.translations.last_message_str}: **{item.message}**</font>\n'
                f"{await self.async_relative_time_received(item.added_at)}.\n\n"
            )

            # Scroll message
            if len(self.message_list_sorted) > 1:
                self.update_scroll_message_pos()

                item: MessageItem = self.message_list_sorted[self.scroll_message_pos]
                self.markdown += (
                    f'- <font color={item.message_level_color}>  <ha-icon icon="{item.icon}"></ha-icon></font> {self.translations.messages_str}: **{item.message}**\n'
                    f"{await self.async_relative_time_received(item.added_at)}. "
                )
        else:
            self.markdown = f'## <font color={MessageLevel.INFO.color}>  <ha-icon icon="mdi:message-outline"></ha-icon></font> {self.translations.message_str}\n'

    # ------------------------------------------------------------------
    def update_scroll_message_pos(self) -> None:
        """Update scroll message pos."""
        if len(self.message_list_sorted) > 1:
            self.scroll_message_pos += 1

            if self.scroll_message_pos >= len(
                self.message_list_sorted
            ) or self.scroll_message_pos >= self.entry.options.get(
                CONF_SCROLL_THROUGH_LAST_MESSAGES_COUNT, 5
            ):
                self.scroll_message_pos = 0
        else:
            self.scroll_message_pos = 0

    # ------------------------------------------------------------------
    async def async_create_markdown_message_list(self) -> None:
        """Markdown message list."""
        # Create markdown list
        if len(self.message_list_sorted) > 0:
            count_pos: int = 1
            self.markdown_message_list = f'## <font color={self.settings.highest_message_level_color}>  <ha-icon icon="mdi:message-outline"></ha-icon></font> {self.translations.messages_str}\n'

            for item in self.message_list_sorted:
                if count_pos > self.entry.options.get(
                    CONF_MARKDOWN_MESSAGE_LIST_COUNT, 10
                ):
                    break

                self.markdown_message_list += (
                    f'- <font color={item.message_level_color}>  <ha-icon icon="{item.icon}"></ha-icon></font> **{item.message}**\n'
                    f"{await self.async_relative_time_received(item.added_at)}.\n"
                )
                count_pos += 1
        else:
            self.markdown_message_list = f'## <font color={MessageLevel.INFO.color}>  <ha-icon icon="mdi:message-outline"></ha-icon></font> {self.translations.message_str}\n'

    # ------------------------------------------------------------------
    async def async_create_markdown_message_settings(self) -> None:
        """Create markdown for settings."""

        orderby: str = (
            self.translations.received_str
            if self.settings.message_list_orderby == MessageListOrderBy.ADDED_AT
            else self.translations.relevance_str
        )

        match self.settings.message_list_show:
            case MessageListShow.ALL:
                show: str = self.translations.all_str
            case MessageListShow.INFO:
                show: str = self.translations.info_str
            case MessageListShow.ATTENTION:
                show: str = self.translations.attention_str
            case MessageListShow.WARNING:
                show: str = self.translations.warning_str
            case MessageListShow.ERROR:
                show: str = self.translations.error_str

        self.markdown_message_settings = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".message_settings",
            orderby=orderby,
            show=show,
        )

        # self.markdown_message_settings = (
        #     "|Opsætning| |\n"
        #     "| --- | ----------- |\n"
        #     f"| Sortering | : {orderby} |\n"
        #     f"| Vis | : {show} |"
        # )

    # ------------------------------------------------------------------
    def create_sorted_message_list(
        self,
        orderby: MessageListOrderBy = MessageListOrderBy.MESSAGE_LEVEL,
        show: MessageListShow = MessageListShow.ALL,
    ) -> None:
        """Create sorted message list."""
        self.message_list_sorted.clear()

        if orderby == MessageListOrderBy.MESSAGE_LEVEL:
            for message_level in reversed(MessageLevel):
                self.message_list_sorted.extend(
                    [
                        x
                        for x in self.settings.message_list
                        if x.message_level == message_level
                        and (
                            show == MessageListShow.ALL
                            or x.message_level.name == show.name
                        )
                    ]
                )

        else:
            self.message_list_sorted.extend(
                [
                    x
                    for x in self.settings.message_list
                    if show == MessageListShow.ALL or x.message_level.name == show.name
                ]
            )

    # ------------------------------------------------------------------
    def get_message(self, num: int = 0) -> str:
        """Get Message."""
        return (
            self.settings.message_list[num].message
            if len(self.settings.message_list) > num
            else ""
        )

    # ------------------------------------------------------------------
    @property
    def message_last(self) -> str:
        """Message last."""
        return self.get_message(0)

    # ------------------------------------------------------------------
    @property
    def message_last_icon(self) -> str:
        """Message last icon."""
        if len(self.settings.message_list) > 0:
            return self.settings.message_list[0].icon

        return "mdi:message-off-outline"

    # ------------------------------------------------------------------
    @property
    def message_level_last(self) -> str:
        """Message level last."""
        return (
            self.settings.message_list[0].message_level.name.capitalize()
            if len(self.settings.message_list) > 0
            else ""
        )

    # ------------------------------------------------------------------
    @property
    def message_level_color_last(self) -> str:
        """Message level color last."""
        return (
            self.settings.message_list[0].message_level.color
            if len(self.settings.message_list) > 0
            else MessageLevel.INFO.color
        )

    # ------------------------------------------------------------------
    @property
    def highest_message_level(self) -> str:
        """Highest message level."""
        return self.settings.highest_message_level.name.capitalize()

    # ------------------------------------------------------------------
    @property
    def message_scroll(self) -> str:
        """Get scroll message."""

        if len(self.settings.message_list) > 1:
            return self.settings.message_list[self.scroll_message_pos].message

        return ""

    # ------------------------------------------------------------------
    @property
    def message_scroll_icon(self) -> str:
        """Get scroll message icon."""

        if len(self.settings.message_list) > 1:
            return self.settings.message_list[self.scroll_message_pos].icon

        return "mdi:message-off-outline"
