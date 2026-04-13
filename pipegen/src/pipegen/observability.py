"""Observability module for tracing and metrics."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

if TYPE_CHECKING:
    from langfuse import Langfuse as LangfuseType
    from langfuse.callback import LangfuseCallbackHandler

try:
    from langfuse import Langfuse
    from langfuse.callback import LangfuseCallbackHandler

    LANGFUSE_AVAILABLE = True
except ImportError:
    Langfuse = None  # type: ignore[misc,assignment]
    LangfuseCallbackHandler = None  # type: ignore[misc,assignment]
    LANGFUSE_AVAILABLE = False


class Observability:
    """Observability manager for OpenTelemetry and Langfuse."""

    def __init__(
        self,
        service_name: str = "pipegen",
        otlp_endpoint: str | None = None,
        langfuse_public_key: str | None = None,
        langfuse_secret_key: str | None = None,
        langfuse_host: str | None = None,
    ):
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint or os.getenv("OTLP_ENDPOINT")
        self.langfuse_public_key = langfuse_public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret_key = langfuse_secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.langfuse_host = langfuse_host or os.getenv("LANGFUSE_HOST")

        self.tracer: trace.Tracer | None = None
        self.langfuse: Langfuse | None = None
        self.langfuse_handler: LangfuseCallbackHandler | None = None

        self._setup_tracing()
        self._setup_langfuse()

    def _setup_tracing(self) -> None:
        """Setup OpenTelemetry tracing."""
        resource = Resource.create({SERVICE_NAME: self.service_name})
        provider = TracerProvider(resource=resource)

        if self.otlp_endpoint:
            try:
                exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info(f"OpenTelemetry tracing enabled, endpoint: {self.otlp_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to setup OTLP exporter: {e}")

        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(self.service_name)

    def _setup_langfuse(self) -> None:
        """Setup Langfuse for LLM observability."""
        if not LANGFUSE_AVAILABLE:
            logger.warning("Langfuse not available, skipping setup")
            return

        if not self.langfuse_public_key or not self.langfuse_secret_key:
            logger.info("Langfuse keys not provided, skipping")
            return

        try:
            self.langfuse = Langfuse(
                public_key=self.langfuse_public_key,
                secret_key=self.langfuse_secret_key,
                host=self.langfuse_host,
            )
            self.langfuse_handler = LangfuseCallbackHandler(
                langfuse=self.langfuse,
            )
            logger.info("Langfuse observability enabled")
        except Exception as e:
            logger.warning(f"Failed to setup Langfuse: {e}")

    def start_span(self, name: str, **attributes):
        """Start a new tracing span."""
        if not self.tracer:
            return None

        span = self.tracer.start_span(name)
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        return span

    def get_langfuse_handler(self) -> LangfuseCallbackHandler | None:
        """Get the Langfuse callback handler for LLM tracing."""
        return self.langfuse_handler


_observability_instance: Observability | None = None


def get_observability() -> Observability:
    """Get or create the global observability instance."""
    global _observability_instance
    if _observability_instance is None:
        _observability_instance = Observability()
    return _observability_instance


def setup_observability(
    service_name: str = "pipegen",
    otlp_endpoint: str | None = None,
    langfuse_public_key: str | None = None,
    langfuse_secret_key: str | None = None,
    langfuse_host: str | None = None,
) -> Observability:
    """Setup and configure observability."""
    global _observability_instance
    _observability_instance = Observability(
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        langfuse_public_key=langfuse_public_key,
        langfuse_secret_key=langfuse_secret_key,
        langfuse_host=langfuse_host,
    )
    return _observability_instance
