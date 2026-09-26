"""Config flow for Bird Feeder Voice Portal integration."""

import logging
from typing import Any, Dict, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CAMERA_NAME,
    CONF_CONVERSATION_AGENT,
    CONF_FRIGATE_URL,
    CONF_PORT,
    CONF_TTS_ENGINE,
    CONF_TTS_VOICE,
    DEFAULT_CAMERA_NAME,
    DEFAULT_CONVERSATION_AGENT,
    DEFAULT_FRIGATE_URL,
    DEFAULT_PORT,
    DEFAULT_TTS_ENGINE,
    DEFAULT_TTS_VOICE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class BirdFeederPortalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bird Feeder Voice Portal."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Prevent duplicate entries for the same port
            await self.async_set_unique_id(f"birdfeeder_portal_{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Bird Feeder Portal (Port {user_input[CONF_PORT]})",
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_FRIGATE_URL, default=DEFAULT_FRIGATE_URL): str,
                vol.Required(CONF_CAMERA_NAME, default=DEFAULT_CAMERA_NAME): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_CONVERSATION_AGENT, default=DEFAULT_CONVERSATION_AGENT): str,
                vol.Required(CONF_TTS_ENGINE, default=DEFAULT_TTS_ENGINE): str,
                vol.Required(CONF_TTS_VOICE, default=DEFAULT_TTS_VOICE): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return BirdFeederPortalOptionsFlowHandler(config_entry)


class BirdFeederPortalOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Bird Feeder Voice Portal."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self.config_entry.data, **self.config_entry.options}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_FRIGATE_URL, default=data.get(CONF_FRIGATE_URL, DEFAULT_FRIGATE_URL)): str,
                vol.Required(CONF_CAMERA_NAME, default=data.get(CONF_CAMERA_NAME, DEFAULT_CAMERA_NAME)): str,
                vol.Required(CONF_PORT, default=data.get(CONF_PORT, DEFAULT_PORT)): int,
                vol.Required(CONF_CONVERSATION_AGENT, default=data.get(CONF_CONVERSATION_AGENT, DEFAULT_CONVERSATION_AGENT)): str,
                vol.Required(CONF_TTS_ENGINE, default=data.get(CONF_TTS_ENGINE, DEFAULT_TTS_ENGINE)): str,
                vol.Required(CONF_TTS_VOICE, default=data.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE)): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
