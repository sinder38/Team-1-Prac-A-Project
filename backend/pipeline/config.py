import tomllib
from pathlib import Path

from pydantic import BaseModel, model_validator


class LLMModelEntry(BaseModel):
    id: str
    slug: str = ""
    name: str = ""
    provider: str = "openrouter"
    max_retries: int | None = None

    @model_validator(mode="after")
    def _fill_derived(self) -> "LLMModelEntry":
        if not self.slug:
            model_id = self.id.split("/", 1)[-1]
            self.slug = model_id.split(":", 1)[0]
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
    models: list[LLMModelEntry] = []
    max_retries: int = 3


class ArtifactsConfig(BaseModel):
    save_json: bool = True
    save_md: bool = True


class StageConfig(BaseModel):
    """Settings shared by command-line and server pipeline stages."""

    llm: LLMConfig = LLMConfig()
    artifacts: ArtifactsConfig = ArtifactsConfig()
    delta: DeltaConfig = DeltaConfig()


class PipelineConfig(StageConfig):
    pipeline: PipelineSection
    stages: StagesConfig


def load_config(path: Path) -> PipelineConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    return PipelineConfig.model_validate(raw)
