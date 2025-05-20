"""The Utec Lock integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api import UtecLockApi
from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN, PLATFORMS
from .coordinator import UtecLockDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Utec Lock component from YAML."""
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, {})
    
    conf = config[DOMAIN]
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data={
                CONF_CLIENT_ID: conf[CONF_CLIENT_ID],
                CONF_CLIENT_SECRET: conf[CONF_CLIENT_SECRET],
            },
        )
    )
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Utec Lock from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create API instance
    api = UtecLockApi(
        client_id=entry.data[CONF_CLIENT_ID],
        client_secret=entry.data[CONF_CLIENT_SECRET],
    )
    
    # Authenticate with the API
    try:
        await hass.async_add_executor_job(api.authenticate)
    except Exception as err:
        _LOGGER.error("Failed to authenticate with Utec API: %s", err)
        return False
    
    # Create coordinator
    coordinator = UtecLockDataUpdateCoordinator(hass, api)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store API and coordinator in hass data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }
    
    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Clean up resources
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            # Close API session
            api = hass.data[DOMAIN][entry.entry_id]["api"]
            if hasattr(api, "session") and api.session:
                await hass.async_add_executor_job(api.session.close)
                
            hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok