import tomllib
from pathlib import Path

from agents.pipeline.config import ArtifactsConfig, StageConfig


class ServerConfig(StageConfig):
    artifacts: ArtifactsConfig = ArtifactsConfig(save_json=False, save_md=False)


def load_server_config(path: Path) -> ServerConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return ServerConfig.model_validate(raw)
