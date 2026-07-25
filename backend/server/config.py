import tomllib
from pathlib import Path

from pydantic import BaseModel

from agents.pipeline.config import ArtifactsConfig, StageConfig


class DatabaseConfig(BaseModel):
    # When true, the server ingests the /data markdown archives into SQLite on
    # startup. When false, the server starts with whatever is already in the DB.
    load_file_data: bool = True


class ServerConfig(StageConfig):
    artifacts: ArtifactsConfig = ArtifactsConfig(save_json=False, save_md=False)
    database: DatabaseConfig = DatabaseConfig()


def load_server_config(path: Path) -> ServerConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return ServerConfig.model_validate(raw)
