"""Load testing helpers for the LiveKit voice agent.

This module provides utilities for running load tests against the LiveKit agent.

For production load testing, use the LiveKit CLI:
    lk perf agent-load-test --url wss://your-server.livekit.cloud \
        --api-key $LIVEKIT_API_KEY \
        --api-secret $LIVEKIT_API_SECRET \
        --num-rooms 50 \
        --duration 300s \
        --publish-audio
"""

import os
import subprocess
import logging

logger = logging.getLogger("load_test")


def run_lk_load_test(
    url: str,
    api_key: str,
    api_secret: str,
    num_rooms: int = 10,
    duration_seconds: int = 300,
    publish_audio: bool = True,
):
    """Run LiveKit CLI load test.

    Args:
        url: LiveKit server URL
        api_key: LiveKit API key
        api_secret: LiveKit API secret
        num_rooms: Number of concurrent rooms
        duration_seconds: Test duration in seconds
        publish_audio: Whether to publish audio
    """
    cmd = [
        "lk",
        "perf",
        "agent-load-test",
        "--url",
        url,
        "--api-key",
        api_key,
        "--api-secret",
        api_secret,
        "--num-rooms",
        str(num_rooms),
        "--duration",
        f"{duration_seconds}s",
    ]

    if publish_audio:
        cmd.append("--publish-audio")

    logger.info(f"Running: {' '.join(cmd)}")

    env = os.environ.copy()
    env["LIVEKIT_URL"] = url
    env["LIVEKIT_API_KEY"] = api_key
    env["LIVEKIT_API_SECRET"] = api_secret

    result = subprocess.run(cmd, env=env)
    return result.returncode


def check_lk_available():
    """Check if LiveKit CLI is available."""
    try:
        result = subprocess.run(
            ["lk", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    if not check_lk_available():
        print("Error: LiveKit CLI (lk) not found.")
        print("Install it from: https://docs.livekit.io/home/cli")
        exit(1)

    url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
    api_key = os.getenv("LIVEKIT_API_KEY", "dev")
    api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")

    print(f"Running load test against: {url}")
    print(f"API Key: {api_key}")

    exit_code = run_lk_load_test(
        url=url,
        api_key=api_key,
        api_secret=api_secret,
        num_rooms=5,
        duration_seconds=60,
    )

    exit(exit_code)
