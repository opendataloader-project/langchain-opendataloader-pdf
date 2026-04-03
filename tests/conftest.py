"""Shared test utilities and fixtures."""

import functools
import subprocess


@functools.lru_cache()
def java_available() -> bool:
    """Check if Java is available on the system."""
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
