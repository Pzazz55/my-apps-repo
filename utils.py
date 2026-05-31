import json
from pathlib import Path

RESULT_FILE = Path("results/attempts.json")


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_results():

    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not RESULT_FILE.exists():
        return []

    try:
        content = RESULT_FILE.read_text(encoding="utf-8").strip()

        if not content:
            return []

        return json.loads(content)

    except Exception:
        return []


def save_result(result):

    results = load_results()
    results.append(result)

    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)