"""API client for Utec Lock integration."""
import logging
import uuid
from typing import Any, Dict, List

import requests

_LOGGER = logging.getLogger(__name__)

class UtecLockApi:
    """API client for Utec Lock integration."""

    def __init__(self, client_id: str, client_secret: str):
        """Initialize the API client."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()
        self.access_token = None
        self.devices = []
        
        # API endpoint
        self.api_url = "https://api.u-tec.com/action"

    def authenticate(self) -> bool:
        """Authenticate with the API."""
        # OAuth authentication request
        headers = {
            "Content-Type": "application/json",
        }
        
        auth_data = {
            "header": {
                "namespace": "Uhome.Auth",
                "name": "Request",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "openapi"
            }
        }
        
        response = self.session.post(
            self.api_url,
            headers=headers,
            json=auth_data,
        )
        
        if response.status_code != 200:
            _LOGGER.error("Authentication failed: %s", response.text)
            return False
            
        result = response.json()
        self.access_token = result.get("payload", {}).get("access_token")
        
        if not self.access_token:
            _LOGGER.error("No access token received")
            return False
            
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        return True

    def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of devices."""
        device_request = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "List",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {}
        }
        
        response = self.session.post(self.api_url, json=device_request)
        
        if response.status_code != 200:
            _LOGGER.error("Failed to get devices: %s", response.text)
            return []
            
        result = response.json()
        self.devices = result.get("payload", {}).get("devices", [])
        return self.devices

    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get device status."""
        status_request = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Status",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {
                "device_id": device_id
            }
        }
        
        response = self.session.post(self.api_url, json=status_request)
        
        if response.status_code != 200:
            _LOGGER.error("Failed to get device status: %s", response.text)
            return {}
            
        return response.json().get("payload", {})

    def get_devices_with_status(self) -> Dict[str, Dict[str, Any]]:
        """Get all devices with their status."""
        devices = self.get_devices()
        devices_with_status = {}
        
        for device in devices:
            device_id = device.get("id")
            if device_id:
                status = self.get_device_status(device_id)
                device["status"] = status
                devices_with_status[device_id] = device
                
        return devices_with_status

    def lock(self, device_id: str) -> bool:
        """Lock the device."""
        lock_request = {
            "header": {
                "namespace": "Uhome.Lock.Control",
                "name": "Lock",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {
                "device_id": device_id
            }
        }
        
        response = self.session.post(self.api_url, json=lock_request)
        
        if response.status_code != 200:
            _LOGGER.error("Failed to lock device: %s", response.text)
            return False
            
        return True

    def unlock(self, device_id: str) -> bool:
        """Unlock the device."""
        unlock_request = {
            "header": {
                "namespace": "Uhome.Lock.Control",
                "name": "Unlock",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {
                "device_id": device_id
            }
        }
        
        response = self.session.post(self.api_url, json=unlock_request)
        
        if response.status_code != 200:
            _LOGGER.error("Failed to unlock device: %s", response.text)
            return False
            
        return True