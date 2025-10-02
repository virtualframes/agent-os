import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.executor import LanguageExecutor


def test_execute_streams_delayed_output():
    executor = LanguageExecutor()
    code = """
import sys
import time

sys.stdout.write('first\\n')
sys.stdout.flush()
time.sleep(0.3)
sys.stdout.write('second\\n')
sys.stdout.flush()
""".strip()

    async def collect_output() -> str:
        chunks = []
        async for chunk in executor.execute(code, "python"):
            chunks.append(chunk)
        return "".join(chunks).replace("\r", "")

    output = asyncio.run(collect_output())

    assert "first\n" in output
    assert "second\n" in output
    assert output.index("first") < output.index("second")
    assert "[Exit code: 0]" in output
