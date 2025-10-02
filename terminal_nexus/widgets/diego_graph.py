from textual.widget import Widget
from textual.reactive import reactive
from rich.panel import Panel
from rich.text import Text
import math
from typing import List, Tuple

class DiegoGraph3D(Widget):
    """3D spacetime visualization of knowledge nodes"""

    rotation = reactive(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nodes: List[Node3D] = []
        self.edges: List[Tuple[int, int, float]] = []  # (from, to, weight)

    class Node3D:
        def __init__(self, x, y, z, label, weight=1.0):
            self.x, self.y, self.z = x, y, z
            self.label = label
            self.weight = weight
            self.color = "cyan"

    def add_node(self, label: str, position: Tuple[float, float, float], weight=1.0):
        """Add knowledge node to spacetime"""
        node = self.Node3D(*position, label, weight)
        self.nodes.append(node)
        # Only add an edge if there's a previous node to connect to
        if len(self.nodes) > 1:
            self.edges.append((len(self.nodes) - 2, len(self.nodes) - 1, weight))
        self.refresh()

    def project_3d_to_2d(self, x, y, z) -> Tuple[int, int]:
        """Rotate and project 3D coords to terminal 2D"""
        # Rotation matrix (simplified)
        angle = self.rotation
        x_rot = x * math.cos(angle) - z * math.sin(angle)
        z_rot = x * math.sin(angle) + z * math.cos(angle)

        # Orthographic projection with depth scaling
        scale = 1.0 / (1.0 + z_rot * 0.1)
        screen_x = int(x_rot * scale * 10 + self.size.width // 2)
        screen_y = int(y * scale * 5 + self.size.height // 2)
        return screen_x, screen_y

    def render(self) -> Panel:
        """Render ASCII 3D graph"""
        canvas = [[' ' for _ in range(self.size.width)]
                  for _ in range(self.size.height)]

        # Draw edges first (depth sorting)
        sorted_edges = sorted(self.edges,
                            key=lambda e: self.nodes[e[0]].z + self.nodes[e[1]].z)

        for from_idx, to_idx, weight in sorted_edges:
            n1, n2 = self.nodes[from_idx], self.nodes[to_idx]
            x1, y1 = self.project_3d_to_2d(n1.x, n1.y, n1.z)
            x2, y2 = self.project_3d_to_2d(n2.x, n2.y, n2.z)

            # Bresenham line drawing
            char = '─' if weight > 0.7 else '·'
            self._draw_line(canvas, x1, y1, x2, y2, char)

        # Draw nodes (on top)
        for node in sorted(self.nodes, key=lambda n: n.z, reverse=True):
            x, y = self.project_3d_to_2d(node.x, node.y, node.z)
            if 0 <= x < self.size.width and 0 <= y < self.size.height:
                symbol = '●' if node.weight > 0.5 else '○'
                canvas[y][x] = symbol

        # Convert to Rich Text with colors
        text = Text()
        for row in canvas:
            line = ''.join(row)
            text.append(line + '\n', style=f"bold {self.nodes[0].color}" if self.nodes else "white")

        return Panel(text, title="[b]Diego Knowledge Graph[/]", border_style="blue")

    def _draw_line(self, canvas, x1, y1, x2, y2, char):
        """Bresenham's line algorithm"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= x1 < len(canvas[0]) and 0 <= y1 < len(canvas):
                canvas[y1][x1] = char
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    async def on_mount(self):
        """Auto-rotate animation"""
        self.set_interval(0.1, self._rotate)

    def _rotate(self):
        self.rotation = (self.rotation + 0.05) % (2 * math.pi)