"""Constants for the Utec Lock integration."""
from homeassistant.const import Platform

# Domain - must match what's in manifest.json
DOMAIN = "utec_lock"

# Configuration parameters
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

# API endpoints
API_URL = "https://api.u-tec.com/action"

# Default values
DEFAULT_SCAN_INTERVAL = 30  # seconds

# Platforms
PLATFORMS = [Platform.LOCK, Platform.SENSOR]