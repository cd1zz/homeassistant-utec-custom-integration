"""Constants for the Utec Lock integration."""
from homeassistant.const import Platform

# Domain
DOMAIN = "utec_lock"

# Platforms
PLATFORMS = [Platform.LOCK, Platform.SENSOR]

# Configuration and options
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

# Default values
DEFAULT_SCAN_INTERVAL = 60  # seconds

# API endpoints
API_BASE_URL = "https://api.u-tec.com/action"