from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

BASE_DIR = Path(__file__).resolve().parent
PROGRAMS_DIR = (BASE_DIR / "programs").resolve()
REGISTRY_PATH = PROGRAMS_DIR / "registry.json"
PROGRAMS_DIR.mkdir(exist_ok=True)

def _load_registry() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"programs": []}

def _save_registry(reg: Dict[str, Any]) -> None:
    PROGRAMS_DIR.mkdir(exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")

def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load module spec")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

def load_module_by_index(idx: int) -> Any:
    path = get_program_path_by_index(idx)
    return load_module(path)

def save_program(code: str) -> Path:
    ts = int(time.time())
    path = PROGRAMS_DIR / f"program_{ts}.py"
    path.write_text(code, encoding="utf-8")
    return path

def register_program(path: Path, spec: Optional[str] = None) -> Dict[str, Any]:
    mod = load_module(path)
    meta = getattr(mod, "__PROGRAM__", None)
    if not isinstance(meta, dict):
        meta = {"name": path.stem, "version": "0.0.0", "description": "no metadata", "params": []}

    item: Dict[str, Any] = {
        "file": str(path),
        "name": str(meta.get("name", path.stem)),
        "version": str(meta.get("version", "0.0.0")),
        "description": str(meta.get("description", "")),
        "kind": str(meta.get("kind", "module")),
        "params": meta.get("params", []),
        "created_at": int(time.time()),
    }
    if spec:
        item["spec"] = spec
    item["history"] = item.get("history", [])
    reg = _load_registry()
    reg["programs"].append(item)
    _save_registry(reg)
    return item

def list_programs() -> List[Dict[str, Any]]:
    return _load_registry().get("programs", [])

def get_program_path_by_index(idx: int) -> Path:
    progs = list_programs()
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")
    return Path(progs[idx]["file"])

def read_program_source_by_index(idx: int) -> str:
    return get_program_path_by_index(idx).read_text(encoding="utf-8")

def overwrite_program_by_index(idx: int, new_code: str, note: str = "") -> Dict[str, Any]:
    reg = _load_registry()
    progs = reg.get("programs", [])
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")

    path = Path(progs[idx]["file"])
    path.write_text(new_code, encoding="utf-8")

    mod = load_module(path)
    meta = getattr(mod, "__PROGRAM__", {})
    if not isinstance(meta, dict):
        meta = {}

    progs[idx]["name"] = str(meta.get("name", progs[idx]["name"]))
    progs[idx]["version"] = str(meta.get("version", progs[idx]["version"]))
    progs[idx]["description"] = str(meta.get("description", progs[idx].get("description", "")))
    progs[idx]["kind"] = str(meta.get("kind", progs[idx].get("kind", "module")))
    progs[idx]["params"] = meta.get("params", progs[idx].get("params", []))
    progs[idx]["updated_at"] = int(time.time())

    if note:
        progs[idx].setdefault("history", []).append({"ts": int(time.time()), "note": note})

    _save_registry(reg)
    return progs[idx]

def delete_program_by_index(idx: int) -> Dict[str, Any]:
    reg = _load_registry()
    progs = reg.get("programs", [])
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")
    item = progs.pop(idx)
    _save_registry(reg)
    try:
        Path(item["file"]).unlink(missing_ok=True)  # type: ignore[arg-type]
    except Exception:
        pass
    return item

def run_program_by_index(idx: int, params: Dict[str, Any]) -> Any:
    mod = load_module_by_index(idx)
    if not hasattr(mod, "run"):
        raise AttributeError("Program has no run(params)")
    return mod.run(params)  # type: ignore
