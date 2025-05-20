"""Lock platform for Utec Lock integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .lock import UtecLock

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Utec locks."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    # Store the session for lock commands
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["session"] = api.session
    
    # Add locks
    locks = []
    for device_id, device in coordinator.data.items():
        # Check if the device is a lock
        if device.get("type") == "lock":
            locks.append(UtecLockCoordinator(coordinator, device_id, device))

    async_add_entities(locks)


class UtecLockCoordinator(CoordinatorEntity, LockEntity):
    """Representation of a Utec Lock that uses the coordinator."""

    def __init__(self, coordinator, device_id, device):
        """Initialize the lock."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._name = device.get("name", f"Utec Lock {device_id}")
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._name,
            manufacturer="U-tec",
            model=device.get("model", "Ultraloq"),
            sw_version=device.get("firmware_version", "Unknown"),
        )
        self._attr_unique_id = f"{DOMAIN}_{device_id}"

    @property
    def name(self):
        """Return the name of the lock."""
        return self._name

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return False
        return device.get("status", {}).get("online", False)

    @property
    def is_locked(self):
        """Return true if the lock is locked."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return None
        
        # Check lock state
        status = device.get("status", {})
        for state in status.get("states", []):
            if state.get("capability") == "st.Lock":
                return state.get("value") == "locked"
        return None

    async def async_lock(self, **kwargs):
        """Lock the device."""
        api = self.coordinator.api
        result = await self.hass.async_add_executor_job(api.lock, self._device_id)
        if result:
            # Trigger a refresh of the coordinator
            await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs):
        """Unlock the device."""
        api = self.coordinator.api
        result = await self.hass.async_add_executor_job(api.unlock, self._device_id)
        if result:
            # Trigger a refresh of the coordinator
            await self.coordinator.async_request_refresh()