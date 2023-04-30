"""Constants for the Custom Integrations Statistics integration."""

from datetime import timedelta

# Integration
DOMAIN = "custstats"
SCAN_INTERVAL = timedelta(hours=1)

# API
STATS_PAGE = "https://analytics.home-assistant.io/custom_integrations.json"

# Config flow
SETUP_INTEGRATION = "integration_domain"
