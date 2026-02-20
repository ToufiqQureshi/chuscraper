import asyncio

from chuscraper.core import util


def test_start_process_wrapper_starts_process() -> None:
    proc = util._start_process("/bin/echo", ["ok"], is_posix=True)
    out, _ = proc.communicate(timeout=2)
    assert b"ok" in out


def test_read_process_stderr_wrapper_returns_text() -> None:
    proc = util._start_process(
        "/bin/sh",
        ["-c", "echo errline 1>&2"],
        is_posix=True,
    )
    stderr = asyncio.run(util._read_process_stderr(proc))
    proc.wait(timeout=2)
    assert "errline" in stderr
