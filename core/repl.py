"""Facade for language-specific REPL implementations."""
from __future__ import annotations

from .repls import REPLManager

__all__ = ["REPLManager"]
