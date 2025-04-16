import asyncio
from temporalio.client import Client

__GLOBAL = {
    "temporal_host": None,
}


def init_temporal(host: str):
    if __GLOBAL["temporal_host"] is not None:
        raise RuntimeError("temporal host already set")
    __GLOBAL["temporal_host"] = host


def get_temporal_host() -> str:
    if __GLOBAL["temporal_host"] is None:
        raise RuntimeError("temporal host not set")
    return __GLOBAL["temporal_host"]


def get_temporal_client():
    host = get_temporal_host()
    return asyncio.run(Client.connect(host))


async def get_temporal_client_async():
    host = get_temporal_host()
    return await Client.connect(host)
