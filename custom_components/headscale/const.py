"""Constants for the Headscale integration."""

import logging
from datetime import timedelta
from typing import Final

DOMAIN: Final = "headscale"
LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL: Final = timedelta(seconds=30)

# Mode constants
MODE_HEADSCALE: Final = "headscale"
MODE_TAILSCALE: Final = "tailscale"

CONF_MODE: Final = "mode"
CONF_URL: Final = "url"
CONF_API_KEY: Final = "api_key"
CONF_VERIFY_SSL: Final = "verify_ssl"

# Tailscale core compatible constants
CONF_TAILNET: Final = "tailnet"
CONF_OAUTH_CLIENT_ID: Final = "oauth_client_id"
CONF_OAUTH_CLIENT_SECRET: Final = "oauth_client_secret"

# Default values
DEFAULT_MODE: Final = MODE_HEADSCALE
DEFAULT_VERIFY_SSL: Final = True

# Service Names
SERVICE_EXPIRE_NODE: Final = "expire_node"
SERVICE_RENAME_NODE: Final = "rename_node"
SERVICE_DELETE_NODE: Final = "delete_node"
SERVICE_SET_NODE_TAGS: Final = "set_node_tags"
SERVICE_SET_APPROVED_ROUTES: Final = "set_approved_routes"
SERVICE_CREATE_PREAUTHKEY: Final = "create_preauthkey"
SERVICE_EXPIRE_PREAUTHKEY: Final = "expire_preauthkey"
SERVICE_CREATE_USER: Final = "create_user"
SERVICE_RENAME_USER: Final = "rename_user"

# Service parameters
ATTR_NODE_ID: Final = "node_id"
ATTR_NEW_NAME: Final = "new_name"
ATTR_TAGS: Final = "tags"
ATTR_ROUTES: Final = "routes"
ATTR_USER: Final = "user"
ATTR_EXPIRATION: Final = "expiration"
ATTR_REUSABLE: Final = "reusable"
ATTR_EPHEMERAL: Final = "ephemeral"
ATTR_KEY: Final = "key"
ATTR_OLD_USER: Final = "old_user"
ATTR_NEW_USER: Final = "new_user"
