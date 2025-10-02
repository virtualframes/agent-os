"""Rust executor implementation."""
from __future__ import annotations

from typing import Iterable

from .base import BaseExecutor


class RustExecutor(BaseExecutor):
    """Compile and execute Rust snippets using ``rustc``."""

    language = "rust"

    @property
    def command(self) -> Iterable[str] | str:
        return ["rustc"]

    @property
    def file_extension(self) -> str:
        return "rs"

    def build_command(self, source_path: str) -> Iterable[str] | str:
        output_path = self._output_path(source_path)
        compile_cmd = ["rustc", source_path, "-o", output_path]
        return f"{self._quote_args(compile_cmd)} && {self._quote_args([output_path])}"


__all__ = ["RustExecutor"]
