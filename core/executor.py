"""Language-aware code execution utilities for Agent-OS.

This module provides an asynchronous interface for executing snippets of
code in a variety of languages. Execution happens inside a pseudo-terminal
(PTY) so the behaviour mirrors an interactive terminal session. Output is
streamed back to the caller to support responsive user interfaces.
"""
from __future__ import annotations

import asyncio
import os
import pty
import shlex
import shutil
import subprocess
import tempfile
from typing import AsyncIterator, Dict, Iterable, List, Optional


class LanguageExecutor:
    """Execute snippets of code across multiple programming languages.

    The executor writes source code to a temporary file and invokes the
    corresponding interpreter or compiler in a PTY-backed subprocess. Output
    is streamed in near real time by yielding chunks from an asynchronous
    generator. A reference to the running process is stored on the instance so
    callers can send signals (e.g. SIGINT) if required.
    """

    #: Mapping of language identifiers to the command used for execution.
    INTERPRETERS: Dict[str, List[str]] = {
        "python": ["python3", "-u"],
        "javascript": ["node"],
        "typescript": ["deno", "run"],
        "rust": ["rustc"],
        "go": ["go", "run"],
        "bash": ["bash"],
        "lua": ["lua"],
        "ruby": ["ruby"],
        "php": ["php"],
    }

    #: File extensions associated with each supported language.
    EXTENSIONS: Dict[str, str] = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "rust": "rs",
        "go": "go",
        "bash": "sh",
        "lua": "lua",
        "ruby": "rb",
        "php": "php",
    }

    def __init__(self) -> None:
        self.current_process: Optional[subprocess.Popen[bytes]] = None

    async def execute(
        self,
        code: str,
        language: str,
        *,
        stdin: Optional[str] = None,
        working_directory: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[str]:
        """Execute *code* written in *language* and stream the output.

        Parameters
        ----------
        code:
            Source code to execute.
        language:
            Identifier for the interpreter/compiler to use.
        stdin:
            Optional standard input that will be sent to the subprocess once it
            has started.
        working_directory:
            Directory from which the command should be executed. Defaults to
            the current working directory of the Python process.
        env:
            Optional environment overrides supplied to ``subprocess.Popen``.

        Yields
        ------
        str
            Chunks of text streamed from the subprocess's stdout/stderr.
        """

        language = language.lower()
        if language not in self.INTERPRETERS:
            yield f"Error: language '{language}' is not supported.\n"
            return

        command = self._build_command(language)
        if not self._command_is_available(command):
            exe = command if isinstance(command, str) else command[0]
            yield f"Error: interpreter '{exe}' is not available on PATH.\n"
            return

        # Persist the code to a temporary file for the interpreter to consume.
        suffix = f".{self.EXTENSIONS.get(language, 'txt')}"
        fd, temp_path = tempfile.mkstemp(suffix=suffix, text=True)
        master_fd: Optional[int] = None
        proc: Optional[subprocess.Popen[bytes]] = None
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(code)

            cmd = self._format_command(command, language, temp_path)
            master_fd, slave_fd = pty.openpty()

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    cwd=working_directory or os.getcwd(),
                    env={**os.environ, **(env or {})},
                    shell=isinstance(cmd, str),
                    close_fds=True,
                )
            except Exception:
                os.close(slave_fd)
                raise
            os.close(slave_fd)
            self.current_process = proc

            # Send any provided stdin once the process has started.
            if stdin:
                await asyncio.to_thread(os.write, master_fd, stdin.encode("utf-8"))

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
            if self.current_process and self.current_process.poll() is None:
                self.current_process.terminate()
                try:
                    await asyncio.to_thread(self.current_process.wait, 2)
                except Exception:
                    self.current_process.kill()
            self.current_process = None
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
                # Drain any remaining data before exiting the loop.
                while True:
                    try:
                        data = await asyncio.to_thread(os.read, master_fd, 1024)
                    except OSError:
                        data = b""
                    if not data:
                        return
                    yield data.decode("utf-8", errors="replace")
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
                yield data.decode("utf-8", errors="replace")

    def _build_command(self, language: str) -> Iterable[str] | str:
        """Return the base command used to execute *language*."""

        command = self.INTERPRETERS[language]
        # Return a copy to avoid mutating the class-level mapping.
        return list(command)

    def _format_command(
        self, command: Iterable[str] | str, language: str, source_path: str
    ) -> Iterable[str] | str:
        """Inject *source_path* into *command* where appropriate."""

        if language == "rust":
            output_path = self._output_path(source_path)
            compile_cmd = ["rustc", source_path, "-o", output_path]
            return f"{self._quote_args(compile_cmd)} && {shlex.quote(output_path)}"

        if isinstance(command, str):
            return command.format(file=source_path, output=self._output_path(source_path))

        formatted: List[str] = []
        for part in command:
            formatted.append(
                part.format(file=source_path, output=self._output_path(source_path))
            )

        formatted.append(source_path)
        return formatted

    def _command_is_available(self, command: Iterable[str] | str) -> bool:
        if isinstance(command, str):
            executable = command.split()[0]
            return shutil.which(executable) is not None
        return shutil.which(command[0]) is not None

    @staticmethod
    def _output_path(source_path: str) -> str:
        base, _ = os.path.splitext(source_path)
        return base

    @staticmethod
    def _quote_args(args: Iterable[str]) -> str:
        return " ".join(shlex.quote(part) for part in args)


__all__ = ["LanguageExecutor"]
