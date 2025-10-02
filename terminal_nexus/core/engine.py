from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, DataTable, Log, Static
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual import events
import httpx
import anthropic
from typing import Dict, Any
import asyncio
import random

from terminal_nexus.widgets.diego_graph import DiegoGraph3D
from terminal_nexus.widgets.services_panel import ServicesPanel
from terminal_nexus.widgets.command_input import CommandInput


class NexusTerminal(App):
    """3D Neural Spacetime Terminal with AI Orchestration"""

    CSS = """
    #diego_graph {
        background: $surface;
        border: solid $primary;
        height: 50%;
    }

    #command_input {
        dock: bottom;
        height: 3;
    }

    #services_panel {
        width: 30%;
        border: solid $accent;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+g", "toggle_graph", "Graph"),
        ("ctrl+m", "memory", "Memory"),
    ]

    def __init__(self):
        super().__init__()
        self.gateway_url = "http://127.0.0.1:8080"
        self.claude = anthropic.Anthropic()
        self.memory_store = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="main_pane"):
                yield DiegoGraph3D(id="diego_graph")
                yield Log(id="output_log", auto_scroll=True)
            yield ServicesPanel(id="services_panel")
        yield CommandInput(id="command_input")
        yield Footer()

    async def on_mount(self):
        """Initialize services and memory"""
        await self.load_memory_context()
        await self.health_check_all()

    async def on_command_input_submitted(self, message: CommandInput.Submitted):
        """Handle submitted commands."""
        command = message.value
        log = self.query_one("#output_log")
        log.write_line(f"> {command}")

        # Add a new node to the 3D graph for visualization
        graph = self.query_one(DiegoGraph3D)
        position = (
            random.uniform(-15, 15),
            random.uniform(-15, 15),
            random.uniform(-15, 15),
        )
        graph.add_node(label=command, position=position, weight=random.random())

        # Send command to gateway
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.gateway_url}/mcp/command",
                    json={"command": command, "context": {}},
                    timeout=30.0,
                )
                resp.raise_for_status()
                response_data = resp.json()
                log.write_line(f"[yellow]MCP Response:[/yellow] {response_data}")
        except httpx.RequestError as e:
            log.write_line(f"[red]Error sending command to gateway: {e}[/red]")
        except Exception as e:
            log.write_line(f"[red]An unexpected error occurred: {e}[/red]")

    async def load_memory_context(self):
        """Load existing knowledge from virtualframes/optimizer memory"""
        try:
            resp = httpx.get(f"{self.gateway_url}/export/qme/leaderboard.json")
            self.memory_store = resp.json()
            self.query_one("#output_log").write_line(
                f"[green]Loaded {len(self.memory_store)} memory artifacts[/]"
            )
        except Exception as e:
            self.query_one("#output_log").write_line(f"[red]Memory load error: {e}[/]")

    async def health_check_all(self):
        """Check all microservices"""
        services = {
            "Gateway": self.gateway_url,
            "Synthesize": "http://127.0.0.1:8017",
            "Priority": "http://127.0.0.1:8015",
            "Scan": "http://127.0.0.1:8021",
            "Rank": "http://127.0.0.1:8013"
        }

        log = self.query_one("#output_log")
        for name, url in services.items():
            try:
                resp = httpx.get(f"{url}/health", timeout=2.0)
                status = "✓" if resp.json().get("ok") else "✗"
                log.write_line(f"{status} {name}")
            except:
                log.write_line(f"✗ {name} [dim](offline)[/]")