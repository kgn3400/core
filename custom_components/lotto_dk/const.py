"""Constants for the Lotto DK integration."""

from enum import Enum
from logging import Logger, getLogger

DOMAIN = "lotto_dk"
DOMAIN_NAME = "Lotto DK"
LOGGER: Logger = getLogger(__name__)

TRANSLATION_KEY = DOMAIN
CONF_EURO_JACKPOT: str = "euro_jackpot"
CONF_LOTTO: str = "lotto"
CONF_VIKING_LOTTO: str = "viking_lotto"

CONF_RESTART_TIMER = "restart_timer"
CONF_LISTEN_TO_TIMER_TRIGGER = "listen_to_timer_trigger"


class RefreshType(Enum):
    """Refresh type."""

    NORMAL = 1
    LISTEN_TO_TIMER_TRIGGER = 2
