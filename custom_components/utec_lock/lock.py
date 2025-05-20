import logging
from homeassistant.components.lock import LockEntity
from .const import DOMAIN, API_URL, DEFAULT_SCAN_INTERVAL
import async_timeout

_LOGGER = logging.getLogger(__name__)

class UtecLock(LockEntity):
    """Representation of a U-tec Ultraloq smart lock."""

    def __init__(self, device_id, name, hass):
        """Initialize the lock."""
        self.device_id = device_id
        self._name = name
        self._is_locked = None
        self.hass = hass
        _LOGGER.debug("Lock entity for %s initialized", self._name)

    @property
    def name(self):
        """Return the name of the lock."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for this entity."""
        return self.device_id

    @property
    def is_locked(self):
        """Return true if the lock is locked."""
        return self._is_locked

    async def async_update(self):
        """Poll the lock state via Uhome.Device.Query."""
        token_session = self.hass.data[DOMAIN]["session"]
        body = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Query",
                "messageId": "uuid-{}".format(self.device_id),
                "payloadVersion": "1"
            },
            "payload": {
                "devices": [{"id": self.device_id}]
            }
        }
        try:
            async with async_timeout.timeout(10):
                resp = await token_session.post(API_URL, json=body)
                res = await resp.json()
        except Exception as e:
            _LOGGER.error("Error querying lock %s: %s", self.device_id, e)
            return

        # Parse state
        devices = res.get("payload", {}).get("devices", [])
        for dev in devices:
            for state in dev.get("states", []):
                if state.get("capability") == "st.Lock":
                    lock_state = state.get("value")
                    self._is_locked = (lock_state == "locked")

    async def async_lock(self, **kwargs):
        """Lock the device via Uhome.Device.Command."""
        token_session = self.hass.data[DOMAIN]["session"]
        body = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Command",
                "messageId": "uuid-{}-lock".format(self.device_id),
                "payloadVersion": "1"
            },
            "payload": {
                "devices": [{
                    "id": self.device_id,
                    "command": {"capability": "st.lock", "name": "lock"}
                }]
            }
        }
        async with async_timeout.timeout(10):
            await token_session.post(API_URL, json=body)
        # Optionally update state or rely on webhook/poll to refresh
        self._is_locked = True

    async def async_unlock(self, **kwargs):
        """Unlock the device via Uhome.Device.Command."""
        token_session = self.hass.data[DOMAIN]["session"]
        body = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Command",
                "messageId": "uuid-{}-unlock".format(self.device_id),
                "payloadVersion": "1"
            },
            "payload": {
                "devices": [{
                    "id": self.device_id,
                    "command": {"capability": "st.lock", "name": "unlock"}
                }]
            }
        }
        async with async_timeout.timeout(10):
            await token_session.post(API_URL, json=body)
        self._is_locked = False

    @property
    def supported_features(self):
        """Flag supported features."""
        # No additional features (e.g. OPEN) beyond lock/unlock
        return 0