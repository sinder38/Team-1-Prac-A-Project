"""Finviz screenshot capture helpers for evidence reports."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Final, Protocol

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.io import week_stem

FINVIZ_FUTURES_URL: Final[str] = "https://finviz.com/futures_performance?v=12"
FINVIZ_SECTORS_URL: Final[str] = "https://finviz.com/published_map?t=sec&st=w1&f=061926&i=sec_w1_230810247"


class ScreenshotProvider(Protocol):
    def capture(self, url: str, path: Path) -> None:
        """Capture url to path as a PNG image."""
        ...


class PlaywrightScreenshotProvider:
    """Capture Finviz pages when Playwright and Chromium are installed."""

    def capture(self, url: str, path: Path) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Screenshot capture requires Playwright. Install it with "
                "`python -m pip install playwright` and then run "
                "`python -m playwright install chromium`."
            ) from exc

        path.parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                page = browser.new_page(
                    viewport={"width": 1600, "height": 1200},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
                    ),
                )
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                try:
                    page.wait_for_load_state("load", timeout=15_000)
                except Exception:
                    pass
                page.wait_for_timeout(3_000)
                page.screenshot(path=str(path), full_page=True)
            finally:
                browser.close()


def screenshot_filenames(prediction_date: date) -> tuple[str, str]:
    week_start = prediction_date - timedelta(days=prediction_date.weekday())
    year = (week_start + timedelta(days=4)).year
    week = week_stem(prediction_date)
    return (
        f"finviz_1W_{year}_{week}.png",
        f"finviz_sectors_5D_{year}_{week}.png",
    )


class EvidenceScreenshotCapturer:
    def __init__(
            self,
            data_root: Path,
            screenshot_provider: ScreenshotProvider | None = None,
            capture_screenshots: bool = True,
            require_screenshots: bool = True,
    ):
        self._data_root = data_root
        self._screenshot_provider = screenshot_provider or PlaywrightScreenshotProvider()
        self._capture_screenshots = capture_screenshots
        self._require_screenshots = require_screenshots

    def capture_finviz_screenshots(self, prediction_date: date) -> tuple[Path, Path]:
        performance_filename, sector_filename = screenshot_filenames(prediction_date)
        evidence_dir = self._data_root / "evidence"
        targets = [
            (FINVIZ_FUTURES_URL, evidence_dir / performance_filename),
            (FINVIZ_SECTORS_URL, evidence_dir / sector_filename),
        ]

        if not self._capture_screenshots:
            return targets[0][1], targets[1][1]

        for url, path in targets:
            try:
                self._screenshot_provider.capture(url, path)
            except Exception as exc:
                message = (
                    f"Could not save required Finviz screenshot for {url} to {path}: {exc}"
                )
                if self._require_screenshots:
                    raise RuntimeError(message) from exc
                print(f"[evidence] screenshot warning: {message}", file=sys.stderr)
        return targets[0][1], targets[1][1]


if __name__ == "__main__":
    import sys

    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    capturer = EvidenceScreenshotCapturer(
        data_root=Path(__file__).resolve().parents[3] / "data",
    )
    performance_path, sector_path = capturer.capture_finviz_screenshots(prediction_date)
    print(f"Saved screenshots:")
    print(f"- {performance_path}")
    print(f"- {sector_path}")