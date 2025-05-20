"""API client for Utec Lock integration."""
import logging
import uuid
from typing import Any, Dict, List
import requests
from .const import API_URL

_LOGGER = logging.getLogger(__name__)

class UtecLockApi:
    """API client for Utec Lock integration."""

    def __init__(self, client_id: str, client_secret: str, access_token: str = None, refresh_token: str = None):
        """Initialize the API client."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.session = requests.Session()
        if access_token:
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        self.devices = []

    def authenticate(self) -> bool:
        """Authenticate with the API using existing tokens or refresh token if needed."""
        if not self.access_token and not self.refresh_token:
            _LOGGER.error("No access token or refresh token available")
            return False
            
        if not self.access_token and self.refresh_token:
            return self.refresh_access_token()
            
        # Validate the existing token by making a simple API request
        test_request = {
            "header": {
                "namespace": "Uhome.System",
                "name": "Check",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {}
        }
        
        try:
            response = self.session.post(API_URL, json=test_request)
            if response.status_code == 200:
                _LOGGER.debug("Authentication successful with existing token")
                return True
            elif response.status_code == 401:  # Unauthorized
                _LOGGER.debug("Access token expired, attempting to refresh")
                return self.refresh_access_token()
            else:
                _LOGGER.error("Authentication failed: %s", response.text)
                return False
        except Exception as e:
            _LOGGER.error("Exception during authentication: %s", e)
            return False

    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        token_url = "https://oauth.u-tec.com/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        try:
            response = self.session.post(token_url, data=data)
            response.raise_for_status()
            result = response.json()
            self.access_token = result.get("access_token")
            self.refresh_token = result.get("refresh_token", self.refresh_token)
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            _LOGGER.debug("Token refreshed successfully")
            return True
        except Exception as e:
            _LOGGER.error("Failed to refresh access token: %s", e)
            return False

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

        try:
            _LOGGER.debug("Getting devices from Utec API")
            response = self.session.post(API_URL, json=device_request)

            if response.status_code != 200:
                _LOGGER.error("Failed to get devices: %s", response.text)
                return []

            result = response.json()
            self.devices = result.get("payload", {}).get("devices", [])
            _LOGGER.debug("Found %s devices", len(self.devices))
            return self.devices

        except Exception as e:
            _LOGGER.error("Exception while getting devices: %s", e)
            return []

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

        try:
            _LOGGER.debug("Getting status for device %s", device_id)
            response = self.session.post(API_URL, json=status_request)

            if response.status_code != 200:
                _LOGGER.error("Failed to get device status: %s", response.text)
                return {}

            return response.json().get("payload", {})

        except Exception as e:
            _LOGGER.error("Exception while getting device status: %s", e)
            return {}

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

        try:
            _LOGGER.debug("Locking device %s", device_id)
            response = self.session.post(API_URL, json=lock_request)

            if response.status_code != 200:
                _LOGGER.error("Failed to lock device: %s", response.text)
                return False

            return True

        except Exception as e:
            _LOGGER.error("Exception while locking device: %s", e)
            return False

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

        try:
            _LOGGER.debug("Unlocking device %s", device_id)
            response = self.session.post(API_URL, json=unlock_request)

            if response.status_code != 200:
                _LOGGER.error("Failed to unlock device: %s", response.text)
                return False

            return True

        except Exception as e:
            _LOGGER.error("Exception while unlocking device: %s", e)
            return False