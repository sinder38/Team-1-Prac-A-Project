from datetime import date
from pathlib import Path

DATA_ROOT = Path(__file__).parent.parent / "data" / "outputs"


def week_stem(prediction_date: date) -> str:
    week = prediction_date.isocalendar()
    return f"W{week.week:02d}"


class FileSaver:
    def __init__(self, out_dir: Path):
        self.out_dir = out_dir

    def save(self, content: str, filename: str) -> Path:
        # TODO: Stop using raw save() method all the time and move to using obstructions
        self.out_dir.mkdir(parents=True, exist_ok=True)
        path = self.out_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    @classmethod
    def for_agent(cls, agent_type: str) -> "FileSaver":
        return cls(DATA_ROOT / agent_type)
