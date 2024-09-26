"""Simple implementation to call Home Assistant REST API."""
# Borrow from https://github.com/custom-components/remote_homeassistant

from typing import Any

from homeassistant import exceptions
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

API_URL = (
    "{proto}://{host}:{port}/api/services/"
    + DOMAIN
    + "/get_remotes?return_response=true"
)


class ApiProblem(exceptions.HomeAssistantError):
    """Error to indicate problem reaching API."""


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class BadResponse(exceptions.HomeAssistantError):
    """Error to indicate a bad response was received."""


class UnsupportedVersion(exceptions.HomeAssistantError):
    """Error to indicate an unsupported version of Home Assistant."""


class EndpointMissing(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


async def async_get_remote_activity_monitors(
    hass, host, port, secure, access_token, verify_ssl
) -> list[dict[str, Any]] | None:
    """Get remote activity monitors."""
    url = API_URL.format(
        proto="https" if secure else "http",
        host=host,
        port=port,
    )
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json",
    }
    session = async_get_clientsession(hass, verify_ssl)

    # Get remote activity monitors
    async with session.post(url, headers=headers) as resp:
        if resp.status == 404:
            raise EndpointMissing
        if 400 <= resp.status < 500:
            raise InvalidAuth
        if resp.status != 200:
            raise ApiProblem
        json = await resp.json()
        if not isinstance(json, dict) or "service_response" not in json:
            raise BadResponse(f"Bad response data: {json}")
        return json["service_response"]["remotes"]
