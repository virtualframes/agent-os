"""Abstract base classes for language-specific executors."""
from __future__ import annotations

import asyncio
import os
import pty
import shlex
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Iterable, Optional


class BaseExecutor(ABC):
    """Base implementation for streaming code execution.

    Subclasses are responsible for providing the interpreter or compiler
    command used to execute a snippet of code and, when necessary, overriding
    :meth:`build_command` to adapt that command to the generated source file.
    The base class handles spawning the subprocess inside a PTY, streaming the
    output back to the caller, and cleaning up resources.
    """

    #: Default encoding used when writing files or decoding output.
    encoding: str = "utf-8"

    def __init__(self) -> None:
        self.current_process: Optional[subprocess.Popen[bytes]] = None

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language identifier handled by this executor."""

    @property
    @abstractmethod
    def command(self) -> Iterable[str] | str:
        """Base command used to execute the generated source file."""

    @property
    def file_extension(self) -> str:
        """File extension used for the temporary source file."""

        return "txt"

    def is_available(self) -> bool:
        """Return ``True`` if the interpreter/compiler is available on PATH."""

        cmd = self.command
        if isinstance(cmd, str):
            executable = cmd.split()[0]
        else:
            executable = cmd[0]
        return shutil.which(executable) is not None

    def extra_environment(self) -> Dict[str, str]:
        """Return environment overrides applied to the subprocess."""

        return {}

    def build_command(self, source_path: str) -> Iterable[str] | str:
        """Return the full command used to execute *source_path*.

        By default the generated source path is appended to the base command.
        Subclasses can override the behaviour (e.g. to compile before
        execution) by implementing this method.
        """

        base = self.command
        if isinstance(base, str):
            return base.format(file=source_path, output=self._output_path(source_path))

        command: list[str] = []
        for part in base:
            command.append(part.format(file=source_path, output=self._output_path(source_path)))
        command.append(source_path)
        return command

    async def execute_stream(
        self,
        code: str,
        *,
        stdin: Optional[str] = None,
        working_directory: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[str]:
        """Execute *code* and yield output chunks as they become available."""

        if not self.is_available():
            cmd = self.command
            executable = cmd if isinstance(cmd, str) else cmd[0]
            yield f"Error: interpreter '{executable}' is not available on PATH.\n"
            return

        suffix = f".{self.file_extension}"
        fd, temp_path = tempfile.mkstemp(suffix=suffix, text=True)
        master_fd: Optional[int] = None
        proc: Optional[subprocess.Popen[bytes]] = None

        try:
            with os.fdopen(fd, "w", encoding=self.encoding) as handle:
                handle.write(code)

            command = self.build_command(temp_path)
            master_fd, slave_fd = pty.openpty()

            try:
                proc = subprocess.Popen(
                    command,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    cwd=working_directory or os.getcwd(),
                    env={**os.environ, **self.extra_environment(), **(env or {})},
                    shell=isinstance(command, str),
                    close_fds=True,
                )
            except Exception:
                os.close(slave_fd)
                raise

            os.close(slave_fd)
            self.current_process = proc

            if stdin:
                await asyncio.to_thread(os.write, master_fd, stdin.encode(self.encoding))

            try:
                async for chunk in self._stream_from_fd(master_fd, proc):
                    yield chunk
            finally:
                if proc is not None:
                    exit_code = proc.poll()
                    if exit_code is None:
                        exit_code = await asyncio.to_thread(proc.wait)
                    yield f"\n[Exit code: {exit_code}]\n"
        finally:
            await self._cleanup(master_fd, temp_path)

    async def terminate(self) -> None:
        """Terminate the currently running subprocess, if any."""

        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()
            try:
                await asyncio.to_thread(self.current_process.wait, 2)
            except Exception:
                self.current_process.kill()
        self.current_process = None

    async def _cleanup(self, master_fd: Optional[int], temp_path: str) -> None:
        await self.terminate()
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        if master_fd is not None:
            try:
                os.close(master_fd)
            except Exception:
                pass

    async def _stream_from_fd(
        self, master_fd: int, proc: subprocess.Popen[bytes]
    ) -> AsyncIterator[str]:
        """Yield decoded chunks from *master_fd* until *proc* exits."""

        while True:
            if proc.poll() is not None:
                while True:
                    try:
                        data = await asyncio.to_thread(os.read, master_fd, 1024)
                    except OSError:
                        data = b""
                    if not data:
                        return
                    yield data.decode(self.encoding, errors="replace")
                return

            try:
                data = await asyncio.wait_for(
                    asyncio.to_thread(os.read, master_fd, 1024), 0.1
                )
            except asyncio.TimeoutError:
                continue
            except OSError:
                data = b""

            if data:
                yield data.decode(self.encoding, errors="replace")

    @staticmethod
    def _output_path(source_path: str) -> str:
        base, _ = os.path.splitext(source_path)
        return base

    @staticmethod
    def _quote_args(args: Iterable[str]) -> str:
        return " ".join(shlex.quote(part) for part in args)


__all__ = ["BaseExecutor"]
