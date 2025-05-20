"""Support for Utec locks."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity 

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Utec lock based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    # Add locks
    locks = []
    for device_id, device in coordinator.data.items():
        # Check if the device is a lock
        if device.get("type") == "lock":
            locks.append(UtecLock(coordinator, api, device_id, device))

    async_add_entities(locks)


class UtecLock(CoordinatorEntity, LockEntity):
    """Representation of a Utec lock."""

    def __init__(self, coordinator, api, device_id, device):
        """Initialize the Utec lock."""
        super().__init__(coordinator)
        self.api = api
        self._device_id = device_id
        self._attr_name = device.get("name", f"Utec Lock {device_id}")
        self._attr_unique_id = f"{DOMAIN}_{device_id}"
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._attr_name,
            manufacturer="U-tec",
            model=device.get("model", "Ultraloq"),
            sw_version=device.get("firmware_version", "Unknown"),
        ) 

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return False
        return device.get("status", {}).get("online", False)

    @property
    def is_locked(self) -> bool | None:
        """Return true if the lock is locked."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return None
        return device.get("status", {}).get("state") == "locked" 

    @property
    def changed_by(self) -> Optional[str]:
        """Return the last entity that changed the lock state."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return None
        return device.get("status", {}).get("last_operated_by") 

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        await self.hass.async_add_executor_job(
            self.api.lock, self._device_id
        )
        await self.coordinator.async_request_refresh() 

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        await self.hass.async_add_executor_job(
            self.api.unlock, self._device_id
        )
        await self.coordinator.async_request_refresh()