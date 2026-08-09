"""
Faithful stubs of dify_plugin.entities.provider_config (SDK v0.7.1),
translated to Python 3.9-compatible syntax.
"""

from enum import Enum


class CredentialType(Enum):
    API_KEY = "api-key"
    OAUTH = "oauth2"
    UNAUTHORIZED = "unauthorized"


class LogMetadata(str, Enum):
    STARTED_AT = "started_at"
    FINISHED_AT = "finished_at"
    ELAPSED_TIME = "elapsed_time"
    TOTAL_PRICE = "total_price"
    TOTAL_TOKENS = "total_tokens"
    PROVIDER = "provider"
    CURRENCY = "currency"
