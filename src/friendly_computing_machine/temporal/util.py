import asyncio
import logging
from typing import Any, Optional, Sequence, Union

from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.contrib.pydantic import pydantic_data_converter

from .naming import init_naming_config, create_workflow_naming

logger = logging.getLogger(__name__)


class __GlobalConfig:
    temporal_host: Optional[str] = None
    queue_prefix: Optional[str] = None  # Deprecated: use naming module instead


def init_temporal(host: str, app_env: str, org: str = "fcm", app: str = "friendly-computing-machine"):
    """
    Initialize temporal configuration with host and naming.
    
    Args:
        host: Temporal server host
        app_env: Environment name (dev, staging, prod, etc.)
        org: Organization identifier (defaults to "fcm")
        app: Application name (defaults to "friendly-computing-machine")
    """
    if __GlobalConfig.temporal_host is not None:
        logger.warning("Temporal host already set, overriding")
    
    __GlobalConfig.temporal_host = host
    
    # Initialize new naming system
    init_naming_config(org=org, app=app, env=app_env)
    
    # Keep backward compatibility
    __GlobalConfig.queue_prefix = f"fcm-{app_env}-"
    
    logger.info("Initialized temporal: host=%s, env=%s, org=%s, app=%s", host, app_env, org, app)


def get_temporal_queue_name(name: str) -> str:
    """
    Get temporal queue name using legacy prefix system.
    
    Note: This function is deprecated. Use the naming module for new workflows.
    """
    # Try new naming system first
    try:
        naming = create_workflow_naming()
        return naming.get_queue_name(name)
    except RuntimeError:
        # Fall back to legacy system for backward compatibility
        if __GlobalConfig.queue_prefix is None:
            raise RuntimeError("temporal queue prefix not set")
        return f"{__GlobalConfig.queue_prefix}{name}"


def get_temporal_host() -> str:
    if __GlobalConfig.temporal_host is None:
        raise RuntimeError("temporal host not set")
    return __GlobalConfig.temporal_host


async def get_temporal_client_async():
    host = get_temporal_host()
    return await Client.connect(
        host,
        data_converter=pydantic_data_converter,
        interceptors=[TracingInterceptor()],
    )


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
