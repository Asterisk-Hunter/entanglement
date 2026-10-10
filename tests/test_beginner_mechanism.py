"""Regression contract for the beginner-facing 'why' reveal.

The technical fingerprint intentionally keeps signed overlap. The beginner
surface must instead explain distinguishability using overlap magnitude while
keeping entanglement visibly MAXIMAL.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX = REPO_ROOT / "index.html"
MAIN = REPO_ROOT / "main.js"
FINGERPRINT = REPO_ROOT / "ui" / "fingerprint.js"


def _d256_metrics() -> dict:
    script = (
        f"const fp = await import('{FINGERPRINT.as_uri()}');"
        "console.log(JSON.stringify(fp.METRICS[256]));"
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_beginner_mechanism_uses_the_same_verified_d256_fixture() -> None:
    metrics = _d256_metrics()
    assert abs(metrics["overlap"]) == 0.9921875
    assert metrics["traceDistance"] == 0.12475562048961962
    assert metrics["executable"] == 0.507781982421875

    source = MAIN.read_text(encoding="utf-8")
    assert "METRICS[experience.dimension]" in source
    assert "Math.abs(metrics.overlap)" in source
    assert "metrics.traceDistance" in source
    assert "metrics.executable" in source


def test_beginner_copy_never_says_entanglement_weakened() -> None:
    markup = INDEX.read_text(encoding="utf-8")
    assert 'id="mechanism-entanglement">MAXIMAL<' in markup
    assert "The resource did not disappear" in markup
    assert "Maximum entanglement stayed maximum" in markup

    lowered = markup.lower()
    for forbidden in ("entanglement weakened", "entanglement decayed", "less entangled"):
        assert forbidden not in lowered


def test_signed_overlap_stays_in_expert_figure_not_beginner_headline() -> None:
    markup = INDEX.read_text(encoding="utf-8")
    source = MAIN.read_text(encoding="utf-8")
    assert "signed overlap is retained in the technical figure" in markup
    assert "OUTPUTS BECAME " in source
    assert "Math.abs(metrics.overlap)" in source
