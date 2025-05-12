import importlib.metadata
import logging
import os
import platform
import socket
import sys
import time
import uuid
from typing import Any, Dict

import typer
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
from opentelemetry.sdk.resources import (
    PROCESS_PID,
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.semconv.resource import (
    ResourceAttributes,
    TelemetrySdkResourceAttributes,
)

logger = logging.getLogger(__name__)
FILENAME = os.path.basename(__file__)


class EnhancedLogFormatter(logging.Formatter):
    """Custom formatter that adds additional context to log records."""

    def __init__(self, fmt=None, datefmt=None, style="%"):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        # Add execution context
        if not hasattr(record, "trace_id"):
            record.trace_id = getattr(record, "trace_id", "")
        if not hasattr(record, "span_id"):
            record.span_id = getattr(record, "span_id", "")

        # Add timestamp in ISO8601 format if not present
        if not hasattr(record, "iso_timestamp"):
            record.iso_timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())

        # Add file info if not present
        if not hasattr(record, "pathname") or not record.pathname:
            record.pathname = record.filename

        return super().format(record)


def get_package_version() -> str:
    """Get the current version of the friendly-computing-machine package."""
    try:
        return importlib.metadata.version("friendly-computing-machine")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def get_resource_attributes() -> Dict[str, Any]:
    """Generate resource attributes for OpenTelemetry."""
    hostname = socket.gethostname()
    instance_id = os.environ.get("INSTANCE_ID", str(uuid.uuid4())[:8])

    attributes = {
        SERVICE_NAME: "friendly-computing-machine",
        SERVICE_VERSION: get_package_version(),
        SERVICE_INSTANCE_ID: instance_id,
        ResourceAttributes.HOST_NAME: hostname,
        ResourceAttributes.OS_TYPE: platform.system().lower(),
        ResourceAttributes.OS_VERSION: platform.version(),
        ResourceAttributes.PROCESS_RUNTIME_NAME: "python",
        ResourceAttributes.PROCESS_RUNTIME_VERSION: platform.python_version(),
        PROCESS_PID: os.getpid(),
        TelemetrySdkResourceAttributes.TELEMETRY_SDK_LANGUAGE: "python",
        TelemetrySdkResourceAttributes.TELEMETRY_SDK_NAME: "opentelemetry",
        "deployment.environment": os.environ.get("ENVIRONMENT", "development"),
    }

    # Add custom attributes
    custom_attrs = {
        "app.start_time": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        "app.command": " ".join(sys.argv),
    }

    attributes.update(custom_attrs)
    return attributes


def setup_logging(
    ctx: typer.Context,
    log_debug: bool = False,
    log_otlp: bool = True,
    log_console: bool = False,
):
    """
    Setup logging for the CLI application with enhanced OpenTelemetry attributes.
    """
    log_level = logging.DEBUG if log_debug else logging.INFO

    # Define detailed log format
    log_format = "%(iso_timestamp)s [%(levelname)s] [%(name)s] [trace_id=%(trace_id)s span_id=%(span_id)s] - %(message)s"
    formatter = EnhancedLogFormatter(log_format)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler for standard logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # OTEL logging setup with rich resource attributes
    logger_provider = LoggerProvider(
        resource=Resource.create(get_resource_attributes()),
    )
    set_logger_provider(logger_provider)

    if log_otlp:
        otlp_exporter = OTLPLogExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT")
            or "http://0.0.0.0:4317",
            insecure=True,
        )
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

    if log_console:
        console_exporter = ConsoleLogExporter()
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(console_exporter)
        )

    # Add OpenTelemetry handler
    otel_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    root_logger.addHandler(otel_handler)

    # Store configuration in context
    ctx.obj[FILENAME] = {
        "log_otlp": log_otlp,
        "log_console": log_console,
        "log_level": "DEBUG" if log_debug else "INFO",
        "resource_attributes": get_resource_attributes(),
    }

    logger.debug(
        "Enhanced logging setup complete",
        extra={
            "setup_time": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "log_config": {
                k: v for k, v in ctx.obj[FILENAME].items() if k != "resource_attributes"
            },
        },
    )


def add_context_to_logs(extra_context: Dict[str, Any]):
    """
    Add additional context to all subsequent log messages.

    Args:
        extra_context: Dictionary of context attributes to add to logs
    """

    class ContextFilter(logging.Filter):
        def filter(self, record):
            for key, value in extra_context.items():
                setattr(record, key, value)
            return True

    context_filter = ContextFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(context_filter)

    logger.debug(
        "Added context to logger", extra={"added_context": list(extra_context.keys())}
    )
