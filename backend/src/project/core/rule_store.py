import json
import os
import re
from datetime import datetime
from pathlib import Path


RULESETS_BASE_DIR = Path(os.getenv("RULESETS_BASE_DIR", "/app/src/project/rulesets"))


def ensure_rulesets_dir() -> None:
    RULESETS_BASE_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_ruleset_code(value: str) -> str:
    value = value.strip().lower()
    value = value.replace(".pdf", "")
    value = re.sub(r"[^a-zа-яё0-9]+", "_", value, flags=re.IGNORECASE)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "ruleset"


def generate_ruleset_code(filename: str) -> str:
    base = sanitize_ruleset_code(filename)
    suffix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{suffix}"


def get_ruleset_path(ruleset_code: str) -> Path:
    return RULESETS_BASE_DIR / f"{ruleset_code}.json"


def save_ruleset(ruleset_code: str, rules: list[dict]) -> Path:
    ensure_rulesets_dir()
    path = get_ruleset_path(ruleset_code)

    with path.open("w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    return path


def load_ruleset_raw(ruleset_code: str) -> list[dict]:
    path = get_ruleset_path(ruleset_code)
    if not path.exists():
        raise FileNotFoundError(f"Набор правил не найден: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_rules(ruleset_code: str) -> list[dict]:
    return load_ruleset_raw(ruleset_code)


def list_available_rulesets() -> list[str]:
    ensure_rulesets_dir()
    return sorted(file.stem for file in RULESETS_BASE_DIR.glob("*.json"))
