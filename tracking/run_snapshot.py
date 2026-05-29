from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = BASE_DIR / "runs"

FILES_TO_SNAPSHOT = [
    (BASE_DIR / "data" / "raw" / "hebbars_kitchen_recipes.json", Path("raw") / "hebbars_kitchen_recipes.json"),
    (BASE_DIR / "data" / "raw" / "web_recipes.json", Path("raw") / "web_recipes.json"),
    (BASE_DIR / "processed_data" / "normalized_recipes.json", Path("processed_data") / "normalized_recipes.json"),
    (BASE_DIR / "processed_data" / "ingredient_catalog.json", Path("processed_data") / "ingredient_catalog.json"),
    (BASE_DIR / "processed_data" / "cuisine_catalog.json", Path("processed_data") / "cuisine_catalog.json"),
    (BASE_DIR / "processed_data" / "accepted_recipes.json", Path("processed_data") / "accepted_recipes.json"),
    (BASE_DIR / "quarantine" / "rejected_recipes.json", Path("quarantine") / "rejected_recipes.json"),
    (BASE_DIR / "tracking" / "url_registry.json", Path("tracking") / "url_registry.json"),
    (BASE_DIR / "tracking" / "source_registry.json", Path("tracking") / "source_registry.json"),
    (BASE_DIR / "data" / "registry.db", Path("data") / "registry.db"),
    (BASE_DIR / "crawl_checkpoint.json", Path("crawl_checkpoint.json")),
]


def safe_json_summary(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"type": "unreadable_json"}

    if isinstance(data, list):
        return {
            "type": "list",
            "count": len(data),
        }

    if isinstance(data, dict):
        summary: Dict[str, Any] = {
            "type": "dict",
            "keys": list(data.keys()),
        }

        for key in ("recipes", "classified_recipes", "top_ingredients", "classified_recipes"):
            if key in data and isinstance(data[key], list):
                summary[f"{key}_count"] = len(data[key])

        return summary

    return {"type": type(data).__name__}


def copy_file(src: Path, dst: Path) -> Optional[Dict[str, Any]]:
    if not src.exists():
        return None

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    info: Dict[str, Any] = {
        "source": str(src),
        "destination": str(dst),
        "size_bytes": dst.stat().st_size,
    }

    json_summary = safe_json_summary(src)
    if json_summary is not None:
        info["json_summary"] = json_summary

    return info


def main() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    run_name = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    copied_files: List[Dict[str, Any]] = []
    missing_files: List[str] = []

    for src, relative_dst in FILES_TO_SNAPSHOT:
        dst = run_dir / relative_dst
        copied = copy_file(src, dst)

        if copied is None:
            missing_files.append(str(src))
        else:
            copied_files.append(copied)

    manifest = {
        "run_name": run_name,
        "created_at": datetime.now().isoformat(),
        "run_dir": str(run_dir),
        "copied_files": copied_files,
        "missing_files": missing_files,
        "total_copied": len(copied_files),
        "total_missing": len(missing_files),
    }

    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Snapshot created: {run_dir}")
    print(f"Copied files    : {len(copied_files)}")
    print(f"Missing files   : {len(missing_files)}")
    print(f"Manifest        : {manifest_path}")


if __name__ == "__main__":
    main()