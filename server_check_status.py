#!/usr/bin/env python3
"""Check whether one server is reachable on one TCP port."""

from __future__ import annotations

import argparse
import socket
import time
from dataclasses import dataclass


DEFAULT_TIMEOUT = 3.0
DEFAULT_PORTS = (
    "80",
    "443",
    "22",
    "21",
    "25",
    "53",
    "110",
    "143",
    "993",
    "995",
    "3306",
    "5432",
    "6379",
    "8080",
    "8443",
)


@dataclass(frozen=True)
class ServerTarget:
    host: str
    port: int

    @property
    def address(self) -> str:
        if ":" in self.host and not self.host.startswith("["):
            return f"[{self.host}]:{self.port}"
        return f"{self.host}:{self.port}"


@dataclass(frozen=True)
class AttemptResult:
    attempt: int
    address: str
    status: str
    latency_ms: float | None
    error: str | None


def parse_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError("Port must be a number.") from exc

    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535.")
    return port


def parse_attempts(value: str) -> int:
    try:
        attempts = int(value)
    except ValueError as exc:
        raise ValueError("Attempts must be a number.") from exc

    if attempts < 1:
        raise ValueError("Attempts must be at least 1.")
    return attempts


def parse_server(value: str) -> str:
    server = value.strip()
    if not server:
        raise ValueError("Server IP or domain name is required.")
    if "://" in server:
        raise ValueError("Enter only the server IP or domain name, without http:// or https://.")
    if server.startswith("[") and server.endswith("]"):
        server = server[1:-1].strip()
    elif server.count(":") == 1:
        raise ValueError("Enter the port number in the Port field, not in the server field.")
    if not server:
        raise ValueError("Server IP or domain name is required.")
    return server


def check_once(target: ServerTarget, attempt: int, timeout: float = DEFAULT_TIMEOUT) -> AttemptResult:
    started = time.perf_counter()

    try:
        with socket.create_connection((target.host, target.port), timeout=timeout):
            latency_ms = (time.perf_counter() - started) * 1000
            return AttemptResult(
                attempt=attempt,
                address=target.address,
                status="available",
                latency_ms=round(latency_ms, 1),
                error=None,
            )
    except OSError as exc:
        return AttemptResult(
            attempt=attempt,
            address=target.address,
            status="unavailable",
            latency_ms=None,
            error=str(exc),
        )


def check_server(target: ServerTarget, attempts: int, timeout: float = DEFAULT_TIMEOUT) -> list[AttemptResult]:
    return [check_once(target, attempt, timeout) for attempt in range(1, attempts + 1)]


def print_results(results: list[AttemptResult]) -> None:
    print(f"{'ATTEMPT':<8} {'STATUS':<12} {'LATENCY':<10} {'ADDRESS':<32} ERROR")
    print(f"{'-' * 8} {'-' * 12} {'-' * 10} {'-' * 32} {'-' * 5}")

    for result in results:
        latency = f"{result.latency_ms:.1f} ms" if result.latency_ms is not None else "-"
        print(f"{result.attempt:<8} {result.status:<12} {latency:<10} {result.address:<32} {result.error or ''}")

    available = sum(1 for result in results if result.status == "available")
    print()
    print(f"Summary: {available} available, {len(results) - available} unavailable")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check one server TCP availability.")
    parser.add_argument("server", help="server IP or domain name to check")
    parser.add_argument(
        "-p",
        "--port",
        required=True,
        help=f"TCP port number to check; common presets: {', '.join(DEFAULT_PORTS)}",
    )
    parser.add_argument("-a", "--attempts", default="1", help="number of attempts to run")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        server = parse_server(args.server)
        port = parse_port(args.port)
        attempts = parse_attempts(args.attempts)
    except ValueError as exc:
        parser.error(str(exc))

    results = check_server(ServerTarget(host=server, port=port), attempts)
    print_results(results)

    return 0 if any(result.status == "available" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
