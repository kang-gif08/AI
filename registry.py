from __future__ import annotations
import importlib.util
import json
import time
from pathlib import Path
from typing import Dict, Any

PROGRAMS_DIR = Path("./programs")
REGISTRY_PATH = PROGRAMS_DIR / "registry.json"
PROGRAMS_DIR.mkdir(exist_ok=True)

# ---------- 内部: レジストリI/O ----------
def _load_registry() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"programs": []}

def _save_registry(reg: Dict[str, Any]) -> None:
    REGISTRY_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- 既存: 新規保存・登録 ----------
def save_program(code: str) -> Path:
    """新規コードを programs/ に保存してパスを返す"""
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
    meta = getattr(mod, "__PROGRAM__", None)
    if not isinstance(meta, dict):
        meta = {"name": path.stem, "version": "0.0.0", "description": "no metadata"}
    item = {
        "file": str(path),
        "name": str(meta.get("name", path.stem)),
        "version": str(meta.get("version", "0.0.0")),
        "description": str(meta.get("description", "")),
        "registered_at": int(time.time()),
    }
    reg = _load_registry()
    reg["programs"].append(item)
    _save_registry(reg)
    return item

def list_programs() -> list[Dict[str, Any]]:
    reg = _load_registry()
    return reg.get("programs", [])

# ---------- 追加: 参照ユーティリティ ----------
def get_program_path_by_index(idx: int) -> Path:
    progs = list_programs()
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")
    return Path(progs[idx]["file"])

def read_program_source_by_index(idx: int) -> str:
    path = get_program_path_by_index(idx)
    return Path(path).read_text(encoding="utf-8")

# ---------- 追加: 上書き（機能追加・変更） ----------
def overwrite_program_by_index(idx: int, new_code: str) -> Dict[str, Any]:
    """
    既存ファイルを“その場所で”上書き。
    上書き後に __PROGRAM__ を再読込し、メタ情報を更新する。
    """
    reg = _load_registry()
    progs = reg.get("programs", [])
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")
    path = Path(progs[idx]["file"])
    path.write_text(new_code, encoding="utf-8")

    # 新メタでエントリ更新
    mod = load_module(path)
    meta = getattr(mod, "__PROGRAM__", None) or {}
    progs[idx]["name"] = str(meta.get("name", path.stem))
    progs[idx]["version"] = str(meta.get("version", progs[idx].get("version", "0.0.0")))
    progs[idx]["description"] = str(meta.get("description", progs[idx].get("description", "")))
    progs[idx]["registered_at"] = int(time.time())  # 更新時刻に差し替え
    _save_registry(reg)
    return progs[idx]

# ---------- 追加: 削除 ----------
def delete_program_by_index(idx: int) -> Dict[str, Any]:
    """
    レジストリから削除し、該当ファイルも削除する（存在しなければ無視）。
    """
    reg = _load_registry()
    progs = reg.get("programs", [])
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")
    item = progs.pop(idx)
    _save_registry(reg)

    # ファイル削除（存在しなければ無視）
    try:
        Path(item["file"]).unlink(missing_ok=True)  # Python 3.8+ は missing_ok あり
    except TypeError:
        p = Path(item["file"])
        if p.exists():
            p.unlink()
    return item

# ---------- 既存: 実行 ----------
def run_program_by_index(idx: int, params: Dict[str, Any]) -> str:
    """レジストリの番号でプログラムを選び run(params) を実行"""
    progs = list_programs()
    if not (0 <= idx < len(progs)):
        raise IndexError("Invalid program index")
    path = Path(progs[idx]["file"])
    mod = load_module(path)
    if not hasattr(mod, "run"):
        raise RuntimeError("Program has no run(params) entrypoint")
    return mod.run(params)  # type: ignore

# 追加: モジュールをインデックスでロード
def load_module_by_index(idx: int):
    path = get_program_path_by_index(idx)
    return load_module(path)
