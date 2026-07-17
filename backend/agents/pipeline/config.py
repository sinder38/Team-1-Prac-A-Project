import tomllib
from pathlib import Path

from pydantic import BaseModel, model_validator


class LLMModelEntry(BaseModel):
    id: str
    slug: str = ""   # short file/path identifier; derived from id if not set in TOML
    name: str = ""   # human-readable label; derived from slug if not set in TOML

    @model_validator(mode="after")
    def _fill_derived(self) -> "LLMModelEntry":
        if not self.slug:
            self.slug = self.id.split("/", 1)[1].split(":")[0]
        if not self.name:
            self.name = self.slug.replace("-", " ").title()
        return self

    @property
    def label(self) -> str:
        return self.name


class PipelineSection(BaseModel):
    prediction_date: str


class StagesConfig(BaseModel):
    almanac: bool = False
    technical: bool = False
    macro: bool = False
    evidence: bool = False
    delta: bool = False


class DeltaConfig(BaseModel):
    prediction_week: str = "previous"
    actuals_week: str = "auto"


class LLMConfig(BaseModel):
    models: list[LLMModelEntry]
    max_retries: int


class ArtifactsConfig(BaseModel):
    save_json: bool = True
    save_md: bool = True


class PipelineConfig(BaseModel):
    pipeline: PipelineSection
    stages: StagesConfig
    delta: DeltaConfig = DeltaConfig()
    llm: LLMConfig
    artifacts: ArtifactsConfig = ArtifactsConfig()


def load_config(path: Path) -> PipelineConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return PipelineConfig.model_validate(raw)
