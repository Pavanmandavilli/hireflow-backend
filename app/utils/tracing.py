from __future__ import annotations

"""
OpenTelemetry tracing helpers.

Install the optional dependency to activate:
    uv add opentelemetry-sdk opentelemetry-instrumentation-fastapi

Then call setup_tracing() inside your lifespan startup.
"""

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


def setup_tracing(service_name: str = "fastapi-service") -> None:
    if not _OTEL_AVAILABLE:
        return
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)


def get_tracer(name: str):
    if not _OTEL_AVAILABLE:
        return _NoOpTracer()
    from opentelemetry import trace
    return trace.get_tracer(name)


class _NoOpTracer:
    """Fallback tracer when OpenTelemetry is not installed."""

    class _NoOpSpan:
        def __enter__(self):
            return self
        def __exit__(self, *_):
            pass

    def start_as_current_span(self, name: str, **_):
        return self._NoOpSpan()
