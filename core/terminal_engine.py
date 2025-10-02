"""Textual-based terminal application scaffold."""

from __future__ import annotations

from typing import Optional

try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Footer, Header, Input, Static
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    App = object  # type: ignore[assignment]
    ComposeResult = object  # type: ignore[assignment]
    Binding = object  # type: ignore[assignment]
    Horizontal = Vertical = object  # type: ignore[assignment]
    Footer = Header = Input = Static = object  # type: ignore[assignment]

from core.graph_engine import SpacetimeGraph
from core.quantum_router import QuantumRouter


class AgentOS(App):  # pragma: no cover - UI scaffolding
    """Cursor-inspired terminal application scaffold.

    The implementation intentionally limits side effects so the class can be
    imported without instantiating Textual's event loop during testing. Real UI
    logic can build on top of this foundation.
    """

    CSS = """
    Screen { background: #11111b; }
    """

    if isinstance(Binding, type):
        BINDINGS = [Binding("ctrl+q", "quit", "Quit")]  # type: ignore[misc]
    else:  # pragma: no cover - Textual missing
        BINDINGS: list = []

    def __init__(
        self,
        router: Optional[QuantumRouter] = None,
        graph: Optional[SpacetimeGraph] = None,
    ) -> None:
        super().__init__()
        self.router = router or QuantumRouter()
        self.graph = graph or SpacetimeGraph()

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header(show_clock=True)
        with Horizontal():  # type: ignore[attr-defined]
            with Vertical(id="left"):  # type: ignore[attr-defined]
                yield Static(
                    "Repository",
                    id="repo",
                )  # type: ignore[attr-defined]
            with Vertical(id="right"):  # type: ignore[attr-defined]
                yield Static(
                    "Output",
                    id="output",
                )  # type: ignore[attr-defined]
        yield Input(
            placeholder="Command...",
            id="command",
        )  # type: ignore[attr-defined]
        yield Footer()  # type: ignore[attr-defined]

    async def on_input_submitted(
        self,
        event: Input.Submitted,
    ) -> None:  # type: ignore[override]
        command = event.value
        result = await self.router.route(command, {"trace_id": "ui"})
        self.graph.add_node(
            command[:32],
            "command",
            {"created_at": ""},
        )
        output = self.query_one(
            "#output",
            Static,
        )  # type: ignore[attr-defined]
        output.update(str(result))


def run() -> None:
    """Entry point used by ``python -m core.terminal_engine``."""

    if App is object:  # pragma: no cover - triggered when Textual is missing
        raise RuntimeError(
            "Textual is not installed; install `textual` to launch the UI."
        )
    AgentOS().run()  # type: ignore[union-attr]
