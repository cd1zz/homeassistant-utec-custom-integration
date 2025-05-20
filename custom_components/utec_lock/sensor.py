"""Sensor platform for Utec Lock integration."""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Utec Lock sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Add battery sensor for each lock
    sensors = []
    for device_id, device in coordinator.data.items():
        # Check if the device is a lock
        if device.get("type") == "lock":
            sensors.append(UtecBatterySensor(coordinator, device_id, device))

    async_add_entities(sensors)


class UtecBatterySensor(CoordinatorEntity, SensorEntity):
    """Battery sensor for a Utec Lock."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC 

    def __init__(self, coordinator, device_id, device):
        """Initialize the battery sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = f"{device.get('name', 'Utec Lock')} Battery"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_battery"
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device.get("name", f"Utec Lock {device_id}"),
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
    def native_value(self) -> int | None:
        """Return the battery level."""
        device = self.coordinator.data.get(self._device_id)
        if not device:
            return None
        return device.get("status", {}).get("battery_level")