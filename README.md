# Utec Lock Integration for Home Assistant

A custom integration for Home Assistant that integrates with Utec (U-tec) smart locks.

## Features

- Lock/unlock functionality
- Battery status monitoring
- Lock status reporting

## Installation

1. Copy this folder to your custom_components directory in Home Assistant
2. Restart Home Assistant
3. Add the following to your configuration.yaml:

```yaml
utec_lock:
  client_id: YOUR_CLIENT_ID
  client_secret: YOUR_CLIENT_SECRET
```
4. Restart Home Assistant again