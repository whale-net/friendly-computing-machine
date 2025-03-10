from alembic.config import Config


class CliContext:
    _instance = None

    def __init__(
        self, slack_app_token: str, alembic_config: Config, google_api_key: str
    ):
        if self._instance is not None:
            raise RuntimeError("context double init")
        CliContext._instance = self
        self.slack_app_token = slack_app_token
        self.alembic_config = alembic_config
        self.google_api_key = google_api_key

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise RuntimeError("context not init")
        return cls._instance
