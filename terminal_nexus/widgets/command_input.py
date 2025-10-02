from textual.widgets import Input
from textual.message import Message

class CommandInput(Input):
    """Natural language command interface"""

    class Submitted(Message):
        def __init__(self, value: str):
            self.value = value
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(
            placeholder="Ask DiegoNalysis anything...",
            **kwargs
        )

    async def on_input_submitted(self, event: Input.Submitted):
        """Process natural language command"""
        command = event.value
        self.value = ""  # Clear input

        # Post message to parent app
        await self.post_message(self.Submitted(command))