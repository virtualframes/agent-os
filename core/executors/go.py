"""Go executor implementation."""
from __future__ import annotations

from typing import Iterable

from .base import BaseExecutor


class GoExecutor(BaseExecutor):
    """Execute Go snippets using ``go run``."""

    language = "go"

    @property
    def command(self) -> Iterable[str] | str:
        return ["go", "run"]

    @property
    def file_extension(self) -> str:
        return "go"


__all__ = ["GoExecutor"]
