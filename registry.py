# registry.py
from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, Any

PROGRAMS_DIR = Path("./programs")
REGISTRY_PATH = PROGRAMS_DIR / "registry.json"
PROGRAMS_DIR.mkdir(exist_ok=True)


def _load_registry() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"programs": []}


def _save_registry(data: Dict[str, Any]) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_program(code: str) -> Path:
    """生成されたプログラムを programs/ に保存してパスを返す"""
    fname = f"program_{int(time.time())}.py"
    path = PROGRAMS_DIR / fname
    path.write_text(code, encoding="utf-8")
    return path


def load_module(path: Path):
    """保存されたプログラムをモジュールとしてロード"""
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def register_program(path: Path) -> Dict[str, Any]:
    """モジュールの __PROGRAM__ を読み取り、レジストリに追記"""
    mod = load_module(path)
    prog = getattr(mod, "__PROGRAM__", None)
    if not isinstance(prog, dict):
        raise ValueError("__PROGRAM__ not found or invalid")

    data = _load_registry()
    entry = {
        "name": prog.get("name", path.stem),
        "version": prog.get("version", "1.0"),
        "description": prog.get("description", ""),
        "file": str(path),
    }
    data["programs"].append(entry)
    _save_registry(data)
    return entry


def list_programs():
    return _load_registry().get("programs", [])


def get_program_path_by_index(idx: int) -> Path:
    progs = list_programs()
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")
    return Path(progs[idx]["file"])


def read_program_source_by_index(idx: int) -> str:
    path = get_program_path_by_index(idx)
    return path.read_text(encoding="utf-8")


def overwrite_program_by_index(idx: int, new_code: str) -> Dict[str, Any]:
    """指定インデックスのプログラムファイルを上書きし、メタ情報も更新"""
    data = _load_registry()
    progs = data.get("programs", [])
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")

    path = Path(progs[idx]["file"])
    path.write_text(new_code, encoding="utf-8")

    mod = load_module(path)
    prog = getattr(mod, "__PROGRAM__", None)
    if not isinstance(prog, dict):
        raise ValueError("__PROGRAM__ not found or invalid after overwrite")

    progs[idx]["name"] = prog.get("name", progs[idx]["name"])
    progs[idx]["version"] = prog.get("version", progs[idx]["version"])
    progs[idx]["description"] = prog.get("description", progs[idx]["description"])
    _save_registry(data)
    return progs[idx]


def delete_program_by_index(idx: int) -> Dict[str, Any]:
    data = _load_registry()
    progs = data.get("programs", [])
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")

    entry = progs.pop(idx)
    _save_registry(data)

    try:
        Path(entry["file"]).unlink(missing_ok=True)  # type: ignore
    except Exception:
        pass

    return entry


def run_program_by_index(idx: int, params: Dict[str, Any]) -> Any:
    """レジストリの番号でプログラムを選び run(params) を実行"""
    path = get_program_path_by_index(idx)
    mod = load_module(path)
    if not hasattr(mod, "run"):
        raise RuntimeError("Program has no run(params) entrypoint")
    return mod.run(params)  # type: ignore


def load_module_by_index(idx: int):
    path = get_program_path_by_index(idx)
    return load_module(path)
