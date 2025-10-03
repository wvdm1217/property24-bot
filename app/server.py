"""HTTP server for exposing Prometheus metrics."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from prometheus_client import REGISTRY, generate_latest

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler
    from typing import Type

logger = logging.getLogger(__name__)


class MetricsHandler:
    """HTTP handler for serving Prometheus metrics."""

    def __init__(self) -> None:
        """Initialize the metrics handler."""
        from http.server import BaseHTTPRequestHandler

        class _Handler(BaseHTTPRequestHandler):
            """Internal HTTP request handler."""

            def do_GET(self) -> None:
                """Handle GET requests."""
                if self.path == "/metrics":
                    self._serve_metrics()
                elif self.path == "/health" or self.path == "/":
                    self._serve_health()
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Not Found")

            def _serve_metrics(self) -> None:
                """Serve Prometheus metrics."""
                try:
                    metrics_data = generate_latest(REGISTRY)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; version=0.0.4")
                    self.end_headers()
                    self.wfile.write(metrics_data)
                except Exception as exc:
                    logger.error("Error generating metrics: %s", exc)
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b"Error generating metrics")

            def _serve_health(self) -> None:
                """Serve health check endpoint."""
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"OK")

            def log_message(self, format: str, *args: object) -> None:
                """Override to use Python logging."""
                logger.debug(format, *args)

        self._handler_class: Type[BaseHTTPRequestHandler] = _Handler

    def get_handler(self) -> Type[BaseHTTPRequestHandler]:
        """Get the handler class."""
        return self._handler_class


def start_metrics_server(port: int = 8000) -> None:
    """Start the Prometheus metrics HTTP server in a background thread.

    Args:
        port: Port to listen on (default: 8000)
    """
    from http.server import HTTPServer
    from socketserver import TCPServer

    handler = MetricsHandler()

    # Enable socket reuse to avoid "Address already in use" errors
    TCPServer.allow_reuse_address = True
    server = HTTPServer(("", port), handler.get_handler())

    def serve() -> None:
        logger.info("Starting metrics server on port %d", port)
        try:
            server.serve_forever()
        except Exception as exc:
            logger.error("Metrics server error: %s", exc)

    thread = threading.Thread(target=serve, daemon=True, name="metrics-server")
    thread.start()
    logger.info("Metrics server started at http://0.0.0.0:%d/metrics", port)
