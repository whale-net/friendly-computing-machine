# if these ever need to be broken up, we can move it into the class for tighter scope
from external.manman_status_api.api.default_api import DefaultApi as StatusDefaultApi
from external.manman_status_api.api_client import ApiClient as StatusApiClient
from external.manman_status_api.configuration import (
    Configuration as StatusConfiguration,
)
from external.old_manman_api.api.default_api import DefaultApi as OldDefaultApi
from external.old_manman_api.api_client import ApiClient as OldApiClient
from external.old_manman_api.configuration import Configuration as OldConfiguration


class BaseManManAPI:
    """Base class for ManMan API clients."""

    _config = None
    _client = None
    _api_client_type = None  # type: ignore
    _api_type = None  # type: ignore

    @classmethod
    def init(cls, host: str):
        """Initialize the API client configuration."""
        if cls._config is not None:
            return
        cls._config = cls._configuration_type(host=host)  # type: ignore
        cls._client = cls._api_client_type(configuration=cls._config)  # type: ignore

    @classmethod
    def _get_client(cls):
        """Get the API client."""
        if cls._client is None:
            raise ValueError(
                f"{cls.__name__} API client not initialized. Call init() first."
            )
        return cls._client

    @classmethod
    def get_api(cls):
        """Get the API instance."""
        return cls._api_type(api_client=cls._get_client())  # type: ignore


class OldManManAPI(BaseManManAPI):
    """Manages the Old ManMan API client configuration and instance."""

    _configuration_type = OldConfiguration
    _api_client_type = OldApiClient
    _api_type = OldDefaultApi


class ManManStatusAPI(BaseManManAPI):
    """Manages the ManMan Status API client configuration and instance."""

    _configuration_type = StatusConfiguration
    _api_client_type = StatusApiClient
    _api_type = StatusDefaultApi
