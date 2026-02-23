import asyncio
import subprocess
from typing import List, Optional

async def run_adb(args: List[str], timeout: float = 10.0) -> str:
    """Executes an ADB command and returns the output."""
    try:
        # Check if adb is available
        process = await asyncio.create_subprocess_exec(
            "adb", *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass # Process already dead
            raise TimeoutError(f"ADB command timed out after {timeout}s: {' '.join(args)}")

        if process.returncode != 0:
            raise RuntimeError(f"ADB Error: {stderr.decode().strip()}")

        return stdout.decode().strip()
    except FileNotFoundError:
        raise RuntimeError("ADB not found. Please install Android Platform Tools.")

async def get_connected_devices() -> List[str]:
    """Returns a list of connected device serials."""
    output = await run_adb(["devices"])
    devices = []
    for line in output.splitlines()[1:]:  # Skip header
        if line.strip():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
    return devices
