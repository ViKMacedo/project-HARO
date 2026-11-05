import json
import re
from pathlib import Path

# backend/app/services/brain.py -> sobe até backend/ e entra em data/
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

CATALOG = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
EMOTIONS = set(CATALOG["emotions"])

_TAG = re.compile(r"^\s*\[([A-Z_]+)\]\s*")


def build_system_prompt() -> str:
    # Relê o arquivo a cada chamada: edite a personalidade e teste sem reiniciar.
    return (DATA_DIR / "personality.md").read_text(encoding="utf-8")

def split_emotion_tag(raw: str) -> tuple[str | None, str]:
    """"Separa '[HAPPY] Olá!' em ('HAPPY',Olá).
    Se a etiqueta faltar, devolve em (None, texto)."""
    match = _TAG.match(raw)
    if match and match.group(1) in EMOTIONS:
        return match.group(1), raw[match.end():].strip()
    return None. _TAG.sub("". raw).strip()
