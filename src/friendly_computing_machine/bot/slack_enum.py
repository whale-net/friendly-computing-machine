from enum import StrEnum


class SlackActionRegistry(StrEnum):
    """
    Enum for Slack action registry.
    """

    MANMAN_WORKER_STOP = "manman_worker_stop"
    # the "server" abstraction via configs is here
    # using "server" as the name throughout this project
    # but keep in mind is has a different meaning in manman-land
    MANMAN_SERVER_CREATE = "manman_server_create"
    MANMAN_SERVER_STDIN = "manman_server_stdin"
    MANMAN_SERVER_STOP = "manman_server_stop"
