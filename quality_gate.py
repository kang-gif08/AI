# quality_gate.py
# 実行前の「自己評価（品質ゲート）」
# - missing import: jarvis_runtime
# - __PROGRAM__/run/paramsスキーマ破損
# - 禁止API: open(), requests, jarvis_runtime.fetch など
# - secretsをparamsに出していないか
# などをチェックする

from __future__ import annotations

import ast
import types
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class GateResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _find_imports(tree: ast.AST) -> Tuple[bool, bool]:
    has_import = False
    has_from_import = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == "jarvis_runtime":
                    has_import = True
        if isinstance(node, ast.ImportFrom) and node.module == "jarvis_runtime":
            has_from_import = True
    return has_import, has_from_import


def _uses_name(tree: ast.AST, name: str) -> bool:
    return any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(tree))


def _has_def(tree: ast.AST, name: str) -> bool:
    return any(isinstance(n, ast.FunctionDef) and n.name == name for n in ast.walk(tree))


def _has_assign_name(tree: ast.AST, name: str) -> bool:
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return True
    return False


def _forbidden_calls(tree: ast.AST) -> List[str]:
    errs: List[str] = []
    for n in ast.walk(tree):
        # open(...)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open":
            errs.append("Forbidden: open() is not allowed; use jarvis_runtime.read_text/write_text")

        # requests.get/post
        if isinstance(n, ast.Attribute) and n.attr in ("get", "post"):
            if isinstance(n.value, ast.Name) and n.value.id == "requests":
                errs.append("Forbidden: requests.* is not allowed; use jarvis_runtime.http_get_json/http_post_json")

        # jarvis_runtime.fetch
        if isinstance(n, ast.Attribute) and n.attr == "fetch":
            if isinstance(n.value, ast.Name) and n.value.id == "jarvis_runtime":
                errs.append("Forbidden: jarvis_runtime.fetch is not allowed; use jarvis_runtime.http_get_json")

    return errs


def _check_program_shape(mod: types.ModuleType) -> List[str]:
    errs: List[str] = []
    prog = getattr(mod, "__PROGRAM__", None)
    if not isinstance(prog, dict):
        return ["__PROGRAM__ must be a dict"]

    if "params" not in prog:
        return ["__PROGRAM__['params'] is missing"]

    params = prog.get("params")
    if not isinstance(params, list):
        return ["__PROGRAM__['params'] must be a list (use [] if no inputs)"]

    for i, item in enumerate(params):
        if not isinstance(item, dict):
            errs.append(f"params[{i}] must be a dict schema object")
            continue

        key = item.get("key")
        if not isinstance(key, str) or not key:
            errs.append(f"params[{i}]['key'] must be a non-empty string")

        typ = item.get("type")
        if not isinstance(typ, str) or not typ:
            errs.append(f"params[{i}]['type'] must be a non-empty string")

        if "required" not in item or not isinstance(item.get("required"), bool):
            errs.append(f"params[{i}]['required'] must be a bool")

        # secretsっぽいキーを禁止（人間に毎回入力させない運用）
        k = key.lower() if isinstance(key, str) else ""
        if k in ("api_key", "apikey", "token", "secret", "key", "access_token", "auth", "authorization"):
            errs.append(
                f"params[{i}]['key']='{key}' looks like a secret. Use jarvis_runtime.get_secret() instead."
            )

    return errs


def gate(code: str) -> GateResult:
    errors: List[str] = []
    warnings: List[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return GateResult(ok=False, errors=[f"SyntaxError: {e}"])

    # 必須構造
    if not _has_assign_name(tree, "__PROGRAM__"):
        errors.append("__PROGRAM__ missing")
    if not _has_def(tree, "run"):
        errors.append("run(params) missing")

    # missing import
    has_import, has_from_import = _find_imports(tree)
    if has_from_import:
        errors.append("Do not use `from jarvis_runtime import ...`; use `import jarvis_runtime`")
    if _uses_name(tree, "jarvis_runtime") and not has_import:
        errors.append("missing import: `import jarvis_runtime`")

    # 禁止API
    errors.extend(_forbidden_calls(tree))

    if errors:
        return GateResult(ok=False, errors=errors, warnings=warnings)

    # 実行して __PROGRAM__ の形を検査
    mod = types.ModuleType("generated_program")
    try:
        exec(compile(code, "<generated>", "exec"), mod.__dict__)
    except Exception as e:
        return GateResult(ok=False, errors=[f"Import/Exec error: {e}"], warnings=warnings)

    errors.extend(_check_program_shape(mod))

    # ちょい警告（強制ではない）
    try:
        if "params[" in code and "params.get(" not in code:
            warnings.append("run() uses params['x'] indexing; consider params.get(...) + explicit required checks.")
    except Exception:
        pass

    return GateResult(ok=(len(errors) == 0), errors=errors, warnings=warnings)


def format_result(r: GateResult) -> str:
    lines: List[str] = []
    lines.append("[OK] 品質ゲートに通過しました。" if r.ok else "[FAIL] 品質ゲートに通っていません。")
    if r.errors:
        lines.append("エラー:")
        lines.extend([f" - {e}" for e in r.errors])
    if r.warnings:
        lines.append("警告:")
        lines.extend([f" - {w}" for w in r.warnings])
    return "\n".join(lines)
