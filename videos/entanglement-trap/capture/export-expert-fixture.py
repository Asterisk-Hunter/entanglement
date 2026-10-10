"""Export the flagship gallery payload for the source-rendered expert drawer."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from channels.api import registered_pair_payloads


OUTPUT = Path(__file__).resolve().parent / "extracted" / "hurts-pair.json"


def main() -> None:
    payload = next(
        pair for pair in registered_pair_payloads()
        if pair["slug"] == "hurts-identity-v"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
