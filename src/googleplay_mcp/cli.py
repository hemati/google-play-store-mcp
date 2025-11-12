"""Command-line interface for running the Google Play MCP server."""

from __future__ import annotations

import argparse
import logging
import os
from typing import Any, Iterable

from .config import Settings
from .server import mcp

LOGGER = logging.getLogger(__name__)

SUPPORTED_TRANSPORTS: set[str] = {"stdio", "sse", "streamable-http", "http"}
HTTP_TRANSPORTS: set[str] = {"sse", "streamable-http", "http"}


def main(argv: Iterable[str] | None = None) -> None:
    """Parse command-line arguments and run the MCP server.

    Args:
        argv: Optional iterable of arguments, primarily useful for tests.
    """

    logging.basicConfig(level=os.environ.get("MCP_CLI_LOG_LEVEL", "INFO").upper())

    args = build_parser().parse_args(list(argv) if argv is not None else None)
    Settings.from_env()  # Fail fast if credentials are not configured correctly.
    run_server(
        transport=args.transport,
        host=args.host,
        port=args.port,
        path=args.path,
        log_level=args.log_level,
        stateless_http=args.stateless_http,
        show_banner=args.show_banner,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        argparse.ArgumentParser: Configured parser instance.
    """

    parser = argparse.ArgumentParser(description="Run the Google Play MCP server")
    parser.add_argument(
        "--transport",
        choices=sorted(SUPPORTED_TRANSPORTS),
        default=None,
        help="Transport to expose (defaults to MCP_TRANSPORT env var or 'stdio').",
    )
    parser.add_argument(
        "--host",
        help="Host interface for HTTP/SSE transports (defaults to MCP_HOST or 0.0.0.0).",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port for HTTP/SSE transports (defaults to MCP_PORT or 8000).",
    )
    parser.add_argument(
        "--path",
        help=(
            "Endpoint path for HTTP/SSE transports. Defaults to MCP_PATH or FastMCP's built-in path."
        ),
    )
    parser.add_argument(
        "--log-level",
        help="Optional log level override for HTTP transports (e.g., info, debug).",
    )
    parser.add_argument(
        "--stateless-http",
        action="store_true",
        default=None,
        help="Enable stateless HTTP mode (or use MCP_STATELESS_HTTP=true).",
    )
    parser.add_argument(
        "--stateful-http",
        dest="stateless_http",
        action="store_false",
        help="Disable stateless HTTP mode explicitly.",
    )
    parser.add_argument(
        "--show-banner",
        dest="show_banner",
        action="store_true",
        default=None,
        help="Display the FastMCP startup banner (default: MCP_SHOW_BANNER or true).",
    )
    parser.add_argument(
        "--no-banner",
        dest="show_banner",
        action="store_false",
        help="Suppress the FastMCP startup banner.",
    )
    return parser


def run_server(
    *,
    transport: str | None = None,
    host: str | None = None,
    port: int | None = None,
    path: str | None = None,
    log_level: str | None = None,
    stateless_http: bool | None = None,
    show_banner: bool | None = None,
) -> None:
    """Run the FastMCP server using CLI or environment configuration.

    Args:
        transport: Desired transport (defaults to MCP_TRANSPORT or ``stdio``).
        host: Host interface when using HTTP transports.
        port: Port for HTTP transports.
        path: Endpoint path for HTTP transports.
        log_level: Optional log level override for HTTP transports.
        stateless_http: Enables stateless HTTP mode for ``streamable-http``.
        show_banner: Whether to display FastMCP's startup banner.
    """

    resolved_transport = _resolve_transport(transport)
    resolved_host = _resolve_host(host, resolved_transport)
    resolved_port = _resolve_port(port)
    resolved_path = path or os.environ.get("MCP_PATH")
    resolved_log_level = log_level or os.environ.get("MCP_LOG_LEVEL")
    resolved_stateless = _resolve_bool_env("MCP_STATELESS_HTTP", stateless_http)
    resolved_banner = _resolve_bool_env("MCP_SHOW_BANNER", show_banner, default=True)

    LOGGER.info(
        "Starting googleplay-mcp with transport=%s host=%s port=%s path=%s",
        resolved_transport,
        resolved_host,
        resolved_port,
        resolved_path,
    )

    run_kwargs: dict[str, Any] = {"show_banner": resolved_banner}

    if resolved_transport in HTTP_TRANSPORTS:
        if resolved_host is not None:
            run_kwargs["host"] = resolved_host
        if resolved_port is not None:
            run_kwargs["port"] = resolved_port
        if resolved_path:
            run_kwargs["path"] = resolved_path
        if resolved_log_level:
            run_kwargs["log_level"] = resolved_log_level
        if resolved_stateless is not None and resolved_transport != "sse":
            run_kwargs["stateless_http"] = resolved_stateless

    mcp.run(transport=resolved_transport, **run_kwargs)


def _resolve_transport(value: str | None) -> str:
    """Resolve the transport from CLI arguments and environment variables.

    Args:
        value: Transport from CLI arguments.

    Returns:
        str: Normalized transport string accepted by FastMCP.

    Raises:
        ValueError: If the transport value is not recognized.
    """

    env_value = os.environ.get("MCP_TRANSPORT")
    candidate = (value or env_value or "stdio").lower()

    if candidate == "http":
        candidate = "streamable-http"

    if candidate not in SUPPORTED_TRANSPORTS:
        raise ValueError(
            f"Unsupported transport '{candidate}'. Choose one of: {sorted(SUPPORTED_TRANSPORTS)}."
        )

    return candidate


def _resolve_host(host: str | None, transport: str) -> str | None:
    """Determine the host binding for HTTP transports.

    Args:
        host: Host supplied via CLI arguments.
        transport: Final transport value.

    Returns:
        Optional[str]: Host string or ``None`` for STDIO transports.
    """

    if transport not in HTTP_TRANSPORTS:
        return None

    env_host = os.environ.get("MCP_HOST")
    return host or env_host or "0.0.0.0"


def _resolve_port(port: int | None) -> int | None:
    """Determine the port for HTTP transports.

    Args:
        port: Port supplied via CLI arguments.

    Returns:
        Optional[int]: Resolved port or ``None`` if not provided.
    """

    if port is not None:
        return port

    env_port = os.environ.get("MCP_PORT")
    if env_port is None:
        return None

    try:
        return int(env_port)
    except ValueError as exc:  # pragma: no cover - defensive, unlikely in tests
        raise ValueError("MCP_PORT must be an integer.") from exc


def _resolve_bool_env(name: str, cli_value: bool | None, *, default: bool | None = None) -> bool | None:
    """Resolve boolean options from CLI and environment variables.

    Args:
        name: Environment variable name.
        cli_value: Value supplied via CLI arguments.
        default: Default value if neither CLI nor environment specify a value.

    Returns:
        Optional[bool]: Resolved boolean value or ``None``.
    """

    if cli_value is not None:
        return cli_value

    env_value = os.environ.get(name)
    if env_value is None:
        return default

    normalized = env_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"Environment variable {name} must be boolean-like, got: {env_value}")


__all__ = [
    "main",
    "build_parser",
    "run_server",
]
