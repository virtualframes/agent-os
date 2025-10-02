"""PHP executor implementation."""
from __future__ import annotations

from typing import Iterable

from .base import BaseExecutor


class PHPExecutor(BaseExecutor):
    """Execute PHP snippets using ``php``."""

    language = "php"

    @property
    def command(self) -> Iterable[str] | str:
        return ["php"]

    @property
    def file_extension(self) -> str:
        return "php"


__all__ = ["PHPExecutor"]
