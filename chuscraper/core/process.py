from __future__ import annotations

import asyncio
import logging
import subprocess
import sys
import atexit
from pathlib import Path
from typing import Any, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .browser import Browser

logger = logging.getLogger(__name__)


# Windows Job Object logic
if sys.platform == "win32":
    import ctypes

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000

    def _assign_to_job_object(process_handle: int) -> Any:
        try:
            job = ctypes.windll.kernel32.CreateJobObjectW(None, None)
            if not job:
                return None

            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

            res = ctypes.windll.kernel32.SetInformationJobObject(
                job,
                9,  # JobObjectExtendedLimitInformation
                ctypes.pointer(info),
                ctypes.sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION),
            )

            if res and ctypes.windll.kernel32.AssignProcessToJobObject(job, process_handle):
                return job
        except Exception as e:
            logger.debug(f"Failed to assign process to job object: {e}")
        return None
else:

    def _assign_to_job_object(process_handle: int) -> Any:
        return None


def register_browser_cleanup(registry: Set[Browser]) -> None:
    """Register process cleanup hook for tracked browser PIDs."""

    def cleanup_registered_browsers() -> None:
        if not registry:
            return

        for browser in list(registry):
            pid = getattr(browser, "_process_pid", None)
            if not pid:
                continue

            try:
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                else:
                    import os
                    import signal

                    os.kill(pid, signal.SIGKILL)
            except Exception:
                pass

    atexit.register(cleanup_registered_browsers)


def start_process(
    exe: str | Path,
    params: list[str],
    is_posix: bool,
) -> subprocess.Popen[bytes]:
    proc = subprocess.Popen(
        [str(exe)] + params,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=is_posix,
    )

    if sys.platform == "win32":
        job = _assign_to_job_object(int(proc._handle))  # type: ignore[attr-defined]
        if job:
            proc._job_handle = job  # type: ignore[attr-defined]

    return proc


async def read_process_stderr(process: subprocess.Popen[bytes], n: int = 2**16) -> str:
    async def read_stderr() -> bytes:
        if process.stderr is None:
            raise ValueError("Process has no stderr")
        return await asyncio.to_thread(process.stderr.read, n)

    try:
        return (await asyncio.wait_for(read_stderr(), 0.25)).decode("utf-8")
    except asyncio.TimeoutError:
        logger.debug("Timeout reading process stderr")
        return ""
