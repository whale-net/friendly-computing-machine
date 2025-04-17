import asyncio
from temporalio.client import Client
from typing import Sequence, Any, Optional, Union
from temporalio.contrib.pydantic import pydantic_data_converter

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


async def get_temporal_client_async():
    host = get_temporal_host()
    return await Client.connect(host, data_converter=pydantic_data_converter)


def execute_workflow(
    runner,
    workflow_args: Optional[Union[Sequence[Any], Any]] = None,
    **kwargs,
):
    return asyncio.run(execute_workflow_async(runner, workflow_args, **kwargs))


async def execute_workflow_async(
    runner,
    args: Optional[Union[Sequence[Any], Any]] = None,
    **kwargs,
):
    client = await get_temporal_client_async()

    # Handle different argument scenarios
    if args is None:
        # No arguments case
        result = await client.execute_workflow(
            runner,
            **kwargs,
        )
    elif isinstance(args, (list, tuple)):
        # Already a sequence - pass directly
        result = await client.execute_workflow(
            runner,
            args=args,
            **kwargs,
        )
    else:
        # Single argument that's not a sequence - wrap it
        result = await client.execute_workflow(
            runner,
            args=[args],
            **kwargs,
        )

    return result
