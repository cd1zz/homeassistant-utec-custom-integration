"""Config flow for Utec Lock integration."""
from __future__ import annotations

import logging
from typing import Any
import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_CLIENT_ID): str,
    vol.Required(CONF_CLIENT_SECRET): str,
})

STEP_CODE_DATA_SCHEMA = vol.Schema({
    vol.Required("authorization_code"): str,
})


def fetch_token(client_id: str, client_secret: str, code: str) -> dict[str, Any] | None:
    """Exchange authorization code for token."""
    token_url = "https://oauth.u-tec.com/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": "http://localhost:9501"
    }
    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        return response.json()
    except Exception as ex:
        _LOGGER.error("Token exchange failed: %s", ex)
        return None


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Utec Lock."""

    VERSION = 1

    def __init__(self) -> None:
        self.client_id: str | None = None
        self.client_secret: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.client_id = user_input[CONF_CLIENT_ID]
            self.client_secret = user_input[CONF_CLIENT_SECRET]

            auth_url = (
                f"https://oauth.u-tec.com/authorize"
                f"?response_type=code"
                f"&client_id={self.client_id}"
                f"&scope=openapi"
                f"&redirect_uri=http%3A%2F%2Flocalhost%3A9501"
                f"&state=123abc"
            )
            _LOGGER.info("Please authorize access via your browser: %s", auth_url)

            return await self.async_step_code()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_code(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle input of authorization code."""
        errors: dict[str, str] = {}

        if user_input is not None:
            auth_code = user_input["authorization_code"]
            token_data = await self.hass.async_add_executor_job(
                fetch_token, self.client_id, self.client_secret, auth_code
            )
            if not token_data:
                errors["base"] = "token_failed"
            else:
                return self.async_create_entry(
                    title="Utec Lock",
                    data={
                        CONF_CLIENT_ID: self.client_id,
                        CONF_CLIENT_SECRET: self.client_secret,
                        "access_token": token_data.get("access_token"),
                        "refresh_token": token_data.get("refresh_token"),
                        "expires_in": token_data.get("expires_in"),
                    },
                )

        return self.async_show_form(
            step_id="code", data_schema=STEP_CODE_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(user_input)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
