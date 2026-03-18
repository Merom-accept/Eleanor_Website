"""
Base worker class. All workers inherit from this.
Each worker streams its response using claude-opus-4-6 with adaptive thinking.
"""

import anthropic
from pathlib import Path

def _load_env():
    """Load .env file if present (no external dependency needed)."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                import os
                os.environ.setdefault(key.strip(), val.strip())

_load_env()


class BaseWorker:
    name: str = "Worker"
    role: str = ""
    system_prompt: str = ""

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.model = "claude-opus-4-6"

    def build_messages(self, context: dict) -> list[dict]:
        """Build the messages list from context. Override in subclasses."""
        raise NotImplementedError

    def run(self, context: dict, verbose: bool = True) -> str:
        """Stream a response and return the full text output."""
        messages = self.build_messages(context)

        if verbose:
            print(f"\n{'='*60}")
            print(f"  {self.name.upper()} — {self.role}")
            print(f"{'='*60}\n")

        full_response = ""

        with self.client.messages.stream(
            model=self.model,
            max_tokens=64000,
            thinking={"type": "adaptive"},
            system=self.system_prompt,
            messages=messages,
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        chunk = event.delta.text
                        full_response += chunk
                        if verbose:
                            print(chunk, end="", flush=True)

        if verbose:
            print(f"\n\n[{self.name} done]\n")

        return full_response
