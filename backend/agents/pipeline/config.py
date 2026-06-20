import tomllib
from pathlib import Path

from pydantic import BaseModel, computed_field


class LLMModelEntry(BaseModel):
    id: str

    @computed_field
    @property
    def slug(self) -> str:
        return self.id.split("/", 1)[1].split(":")[0]

    @computed_field
    @property
    def label(self) -> str:
        return self.slug.replace("-", " ").title()


class PipelineSection(BaseModel):
    prediction_date: str


class StagesConfig(BaseModel):
    almanac: bool = False
    technical: bool = False
    macro: bool = False
    evidence: bool = False


class LLMConfig(BaseModel):
    models: list[LLMModelEntry]


class ArtifactsConfig(BaseModel):
    save_json: bool = True
    save_md: bool = True


class PipelineConfig(BaseModel):
    pipeline: PipelineSection
    stages: StagesConfig
    llm: LLMConfig
    artifacts: ArtifactsConfig = ArtifactsConfig()


def load_config(path: Path) -> PipelineConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return PipelineConfig.model_validate(raw)
