"""Bash executor implementation."""
from __future__ import annotations

from typing import Iterable

from .base import BaseExecutor


class BashExecutor(BaseExecutor):
    """Execute shell snippets using ``bash``."""

    language = "bash"

    @property
    def command(self) -> Iterable[str] | str:
        return ["bash"]

    @property
    def file_extension(self) -> str:
        return "sh"


__all__ = ["BashExecutor"]
