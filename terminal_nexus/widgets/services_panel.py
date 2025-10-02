from textual.widgets import Static, DataTable, Log
from textual.reactive import reactive
from textual.containers import ComposeResult
import httpx
import time
import asyncio
from typing import Dict

class ServicesPanel(Static):
    """Real-time microservices health dashboard"""

    services_status = reactive({})

    def compose(self) -> ComposeResult:
        yield DataTable(id="services_table")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Service", "Status", "Latency")

        # Auto-refresh every 5 seconds
        self.set_interval(5.0, self.refresh_services)
        # Initial refresh
        self.app.call_later(self.refresh_services)

    async def refresh_services(self):
        """Poll all microservices and update status."""
        services = {
            "Gateway": "http://127.0.0.1:8080",
            "MCP Router": "http://127.0.0.1:8090",
            "Synthesize": "http://127.0.0.1:8017",
            "Priority": "http://127.0.0.1:8015",
            "Scan": "http://127.0.0.1:8021",
            "Rank": "http://127.0.0.1:8013"
        }

        new_status = {}

        async with httpx.AsyncClient(timeout=2.0) as client:
            tasks = []
            for name, url in services.items():
                tasks.append(self._check_service(client, name, url))

            results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                # This part is tricky as we don't know which service failed.
                # A more robust implementation would map tasks to services.
                # For now, we assume order is preserved.
                pass
            else:
                new_status.update(res)

        self.services_status = new_status

    async def _check_service(self, client: httpx.AsyncClient, name: str, url: str) -> dict:
        """Helper to check a single service."""
        status_data = {"ok": False, "latency_ms": 0}
        start_time = time.perf_counter()
        try:
            resp = await client.get(f"{url}/health")
            latency_ms = (time.perf_counter() - start_time) * 1000
            status_data["latency_ms"] = latency_ms
            if resp.status_code == 200 and resp.json().get("ok"):
                status_data["ok"] = True
        except httpx.RequestError:
            status_data["ok"] = False

        return {name: status_data}

    def watch_services_status(self, status: Dict[str, Dict]):
        """Update table when status changes"""
        table = self.query_one(DataTable)
        table.clear()

        for svc, data in status.items():
            table.add_row(
                svc,
                "✓" if data["ok"] else "✗",
                f"{data.get('latency_ms', 0):.1f}ms"
            )