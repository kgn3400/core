"""Constants for Hiper driftsstatus DK integration."""

from logging import Logger, getLogger

DOMAIN = "hiper_drift"
DOMAIN_NAME = "Hiper drift"
LOGGER: Logger = getLogger(__name__)

TRANSLATION_KEY = DOMAIN
CONF_REGION = "region"
CONF_CITY = "city"
CONF_CITY_CHECK = "city_check"
CONF_STREET = "street"
CONF_STREET_CHECK = "street_check"
CONF_GENERAL_MSG = "general_msg"
CONF_SJ_BH = "Sjælland og Bonholm"
CONF_FYN = "Fyn"
CONF_JYL = "Jylland"
CONF_MSG = "message"
CONF_CONTENT = "content"

TRANSLATION_KEY_REGION = "region"
CONF_SJ_BH_REGION = "sj_bh"
CONF_FYN_REGION = "fyn"
CONF_JYL_REGION = "jylland"
