"""JavaScript executor using Node.js."""
from __future__ import annotations

from typing import Iterable

from .base import BaseExecutor


class JavaScriptExecutor(BaseExecutor):
    """Execute JavaScript snippets via Node.js."""

    language = "javascript"

    @property
    def command(self) -> Iterable[str] | str:
        return ["node"]

    @property
    def file_extension(self) -> str:
        return "js"


__all__ = ["JavaScriptExecutor"]
