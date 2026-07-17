import tomllib
from pathlib import Path

from pydantic import BaseModel

from agents.pipeline.config import ArtifactsConfig, LLMModelEntry


class ServerLLMConfig(BaseModel):
    models: list[LLMModelEntry] = []
    max_retries: int = 3


class ServerConfig(BaseModel):
    llm: ServerLLMConfig = ServerLLMConfig()
    artifacts: ArtifactsConfig = ArtifactsConfig(save_json=False, save_md=False)


def load_server_config(path: Path) -> ServerConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return ServerConfig.model_validate(raw)
