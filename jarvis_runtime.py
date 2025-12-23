# jarvis_runtime.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json
import requests

from registry import list_programs, run_program_by_index

# 安全な作業ディレクトリ
WORKSPACE_ROOT = Path("./workspace").resolve()
PROGRAMS_ROOT = Path("./programs").resolve()
SECRETS_DIR = (WORKSPACE_ROOT / "secrets").resolve()

WORKSPACE_ROOT.mkdir(exist_ok=True)
SECRETS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_path(base: Path, relative: str) -> Path:
    """../ などで外へ出ないための安全なパス解決。"""
    p = (base / relative).resolve()
    if not str(p).startswith(str(base)):
        raise ValueError("Unsafe path escape blocked")
    return p


# -------------------------------
# Secrets (workspace/secrets)
# -------------------------------
def get_secret(name: str, default: Optional[str] = None) -> str:
    """
    Read a secret from ./workspace/secrets/<name>.txt
    例: get_secret("WEATHER_API_KEY")
    """
    filename = f"{name}.txt" if not name.endswith(".txt") else name
    p = _safe_path(SECRETS_DIR, filename)
    if not p.exists():
        if default is not None:
            return str(default)
        raise FileNotFoundError(f"Secret not found: {p}")
    return p.read_text(encoding="utf-8").strip()


# -------------------------------
# ファイル I/O（読み書き）
# -------------------------------
def read_text(rel: str, from_workspace: bool = True) -> str:
    base = WORKSPACE_ROOT if from_workspace else PROGRAMS_ROOT
    p = _safe_path(base, rel)
    if not p.exists():
        raise FileNotFoundError(f"{p} not found")
    return p.read_text(encoding="utf-8")


def write_text(rel: str, content: str, to_workspace: bool = True) -> str:
    base = WORKSPACE_ROOT if to_workspace else PROGRAMS_ROOT
    p = _safe_path(base, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return str(p)


def read_json(rel: str, from_workspace: bool = True) -> Any:
    return json.loads(read_text(rel, from_workspace))


def write_json(rel: str, obj: Any, to_workspace: bool = True) -> str:
    return write_text(rel, json.dumps(obj, ensure_ascii=False, indent=2), to_workspace)


# -------------------------------
# ツール（プログラム）呼び出し
# -------------------------------
def call_program_by_index(idx: int, params: Dict[str, Any]) -> Any:
    return run_program_by_index(idx, params)


def call_program_by_name(name: str, params: Dict[str, Any]) -> Any:
    for i, p in enumerate(list_programs()):
        if p.get("name") == name:
            return run_program_by_index(i, params)
    raise ValueError(f"Program '{name}' not found")


# -------------------------------
# Web API ラッパー
# -------------------------------
def http_get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10):
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        return resp.text


def http_post_json(url: str, data: Any, timeout: float = 10):
    resp = requests.post(url, json=data, timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        return resp.text


# -------------------------------
# Backward compat (deprecated)
# -------------------------------
def fetch(url: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10):
    """
    互換用（非推奨）: 既存プログラムが jarvis_runtime.fetch を呼んでも落ちないために残す。
    新規生成は quality_gate で禁止して http_get_json に寄せる。
    """
    return http_get_json(url, params=params, timeout=timeout)
