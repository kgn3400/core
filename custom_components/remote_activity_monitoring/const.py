"""Constants for Ping alert integration."""

from enum import StrEnum
from logging import Logger, getLogger

DOMAIN = "remote_activity_monitoring"
DOMAIN_NAME = "Remote activity monitoring"
LOGGER: Logger = getLogger(__name__)

TRANSLATION_KEY = DOMAIN
TRANSLATION_KEY_MISSING_ENTITY = "missing_entity"
TRANSLATION_KEY_MISSING__TIMER_ENTITY = "missing_timer_entity"
TRANSLATION_KEY_TEMPLATE_ERROR = "template_error"

CONF_COMPONENT_TYPE = "component_type"
CONF_SECURE = "secure"
CONF_MONITOR_ENTITY = "monitor_entity"


CONF_ENTITY_IDS = "entity_ids"

STATE_INIT = "initializing"
STATE_CONNECTING = "connecting"
STATE_CONNECTED = "connected"
STATE_AUTH_INVALID = "auth_invalid"
STATE_AUTH_REQUIRED = "auth_required"
STATE_RECONNECTING = "reconnecting"
STATE_DISCONNECTED = "disconnected"

DEFAULT_MAX_MSG_SIZE = 16 * 1024 * 1024
HEARTBEAT_INTERVAL = 20
HEARTBEAT_TIMEOUT = 5


class ComponentType(StrEnum):
    """Available entity component types."""

    MAIN = "main"
    REMOTE = "remote"


class StepType(StrEnum):
    """Available entity component types."""

    CONFIG = "config"
    OPTIONS = "options"
