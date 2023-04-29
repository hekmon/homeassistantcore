"""Constants for the Custom Integrations Statistics integration."""

import datetime

DOMAIN = "custstats"

# API
STATS_PAGE = "https://analytics.home-assistant.io/custom_integrations.json"
REFRESH_INTERVAL = datetime.timedelta(hours=1)

# Config flow
SETUP_INTEGRATION = "integration_domain"
