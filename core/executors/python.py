"""Python executor implementation."""
from __future__ import annotations

from typing import Iterable

from .base import BaseExecutor


class PythonExecutor(BaseExecutor):
    """Execute Python snippets using the system interpreter."""

    language = "python"

    @property
    def command(self) -> Iterable[str] | str:
        return ["python3", "-u"]

    @property
    def file_extension(self) -> str:
        return "py"


__all__ = ["PythonExecutor"]
