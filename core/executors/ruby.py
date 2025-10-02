"""Ruby executor implementation."""
from __future__ import annotations

from typing import Iterable

from .base import BaseExecutor


class RubyExecutor(BaseExecutor):
    """Execute Ruby snippets using ``ruby``."""

    language = "ruby"

    @property
    def command(self) -> Iterable[str] | str:
        return ["ruby"]

    @property
    def file_extension(self) -> str:
        return "rb"


__all__ = ["RubyExecutor"]
