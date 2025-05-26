from typing import Optional  # Import Optional

from external.old_manman_api.api.default_api import DefaultApi
from external.old_manman_api.api_client import ApiClient
from external.old_manman_api.configuration import Configuration


class ManManAPI:
    """Manages the ManMan API client configuration and instance."""

    _config: Optional[Configuration] = None
    _client: Optional[ApiClient] = None

    @classmethod
    def init(cls, manman_host: str):
        """
        Initialize the API client configuration with the given ManMan host URL.
        Prevents re-initialization.
        """
        if cls._config is not None:
            return
        cls._config = Configuration(host=manman_host)
        cls._client = ApiClient(configuration=cls._config)

    @classmethod
    def _get_client(cls) -> ApiClient:
        """
        Get the API client for the ManMan host API.
        Initializes the client lazily on first call after configuration.
        Raises ValueError if not initialized.
        """
        if cls._client is None:
            raise ValueError("ManMan API client not initialized. Call init() first.")
        return cls._client

    @classmethod
    def get_api(cls) -> DefaultApi:
        """
        Get the DefaultApi instance for the ManMan API.
        """
        return DefaultApi(api_client=cls._get_client())
