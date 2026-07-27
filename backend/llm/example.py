"""
Example LLM Agent — template for implementing a BaseLLMAgent subclass.

Copy this file, rename it to {your_model}_agent.py, and fill in query().

Usage:
    python agents/llm/example_agent.py 2026-06-16
"""
from datetime import date
from pathlib import Path
import sys


from llm.base import BaseLLMAgent


class ExampleAgent(BaseLLMAgent):
    model_name = "example"  # change this to your model name

    def query(self, prompt: str) -> str:
        """
        Send prompt to your LLM and return the raw text response.

        Options:
          - Call an official API (e.g. anthropic, openai)
          - Call a local model (e.g. via ollama: requests.post("http://localhost:11434/api/generate", ...))
          - Use an unofficial client library
          - Read from a local .txt file you filled in manually (last resort):
              return Path("my_response.txt").read_text(encoding="utf-8")
        """
        raise NotImplementedError("Implement query() with your LLM access method")


if __name__ == "__main__":
    from core.io import FileSaver, week_stem

    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    agent = ExampleAgent()
    output = agent.run(prediction_date)
    saver = FileSaver(Path(__file__).parent.parent.parent / "data" / "outputs" / "llm" / agent.model_name)
    saver.save(agent.render_json(output, prediction_date), f"{week_stem(prediction_date)}_{agent.model_name}.json")
    print(f"Saved to data/outputs/llm/{agent.model_name}/")
