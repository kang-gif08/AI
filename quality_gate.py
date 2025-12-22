# quality_gate.py
from __future__ import annotations

import ast
import importlib.util
import re
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

import jarvis_runtime

_REQUIRED_META_KEYS = ["name", "version", "description", "params"]
_PARAM_REQUIRED_KEYS = ["key", "type", "required"]

@dataclass
class TestResult:
    name: str
    ok: bool
    error: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GateResult:
    ok: bool
    errors: List[str]
    warnings: List[str]
    tests: List[TestResult]
    score: int = 0
    score_breakdown: Dict[str, Any] = field(default_factory=dict)

def _is_dict_str_str(x: Any) -> bool:
    return isinstance(x, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in x.items())

def _validate_params_schema(schema: Any, errors: List[str], warnings: List[str]) -> None:
    if not isinstance(schema, list):
        errors.append(f"__PROGRAM__['params'] must be a list, got {type(schema).__name__}")
        return
    if len(schema) > 8:
        warnings.append(f"params length is large ({len(schema)}). Consider <= 5 for composability.")
    for i, item in enumerate(schema):
        if not isinstance(item, dict):
            errors.append(f"params[{i}] must be a dict, got {type(item).__name__}")
            continue
        for k in _PARAM_REQUIRED_KEYS:
            if k not in item:
                errors.append(f"params[{i}] missing required key '{k}'")
        key = item.get("key")
        if isinstance(key, str) and "api_key" in key.lower():
            errors.append("params must not include api_key (use jarvis_runtime.get_secret instead)")

def _validate_program_meta(meta: Any) -> Tuple[Dict[str, Any], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(meta, dict):
        errors.append(f"__PROGRAM__ must be a dict, got {type(meta).__name__}")
        return {}, errors, warnings

    for k in _REQUIRED_META_KEYS:
        if k not in meta:
            errors.append(f"__PROGRAM__ missing '{k}'")

    if "params" in meta:
        _validate_params_schema(meta.get("params"), errors, warnings)

    desc = meta.get("description", "")
    if isinstance(desc, str) and len(desc.strip()) < 10:
        warnings.append("description is short; consider adding clearer purpose/output info.")

    return meta, errors, warnings

@contextmanager
def _patched_runtime(
    mock_secrets: Optional[Dict[str, str]] = None,
    mock_http_get: Optional[Any] = None,
    mock_http_post: Optional[Any] = None
):
    orig_get_secret = getattr(jarvis_runtime, "get_secret", None)
    orig_http_get = getattr(jarvis_runtime, "http_get_json", None)
    orig_fetch = getattr(jarvis_runtime, "fetch", None)
    orig_http_post = getattr(jarvis_runtime, "http_post_json", None)

    def _get_secret(name: str) -> str:
        if mock_secrets and name in mock_secrets:
            return mock_secrets[name]
        if callable(orig_get_secret):
            return orig_get_secret(name)  # type: ignore
        raise AttributeError("jarvis_runtime.get_secret is not available")

    def _http_get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10) -> Any:
        if mock_http_get is not None:
            return mock_http_get
        if callable(orig_http_get):
            return orig_http_get(url, params=params, timeout=timeout)  # type: ignore
        raise AttributeError("jarvis_runtime.http_get_json is not available")

    def _http_post_json(url: str, data: Any, timeout: float = 10) -> Any:
        if mock_http_post is not None:
            return mock_http_post
        if callable(orig_http_post):
            return orig_http_post(url, data=data, timeout=timeout)  # type: ignore
        raise AttributeError("jarvis_runtime.http_post_json is not available")

    try:
        if orig_get_secret is not None:
            jarvis_runtime.get_secret = _get_secret  # type: ignore
        if orig_http_get is not None:
            jarvis_runtime.http_get_json = _http_get_json  # type: ignore
        if orig_fetch is not None:
            jarvis_runtime.fetch = _http_get_json  # type: ignore
        if orig_http_post is not None:
            jarvis_runtime.http_post_json = _http_post_json  # type: ignore
        yield
    finally:
        if orig_get_secret is not None:
            jarvis_runtime.get_secret = orig_get_secret  # type: ignore
        if orig_http_get is not None:
            jarvis_runtime.http_get_json = orig_http_get  # type: ignore
        if orig_fetch is not None:
            jarvis_runtime.fetch = orig_fetch  # type: ignore
        if orig_http_post is not None:
            jarvis_runtime.http_post_json = orig_http_post  # type: ignore

def load_module_from_code(code: str, tmp_name: str = "_jarvis_tmp_program") -> Any:
    tmp_rel = f"tmp/{tmp_name}.py"
    jarvis_runtime.write_text(tmp_rel, code, to_workspace=True)
    path = (jarvis_runtime.WORKSPACE_ROOT / tmp_rel).resolve()

    spec = importlib.util.spec_from_file_location(tmp_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to create module spec")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

def _analyze_ast(code: str) -> Dict[str, Any]:
    info = {
        "has_program": False,
        "has_run": False,
        "run_has_try": False,
        "run_has_return": False,
        "uses_params_get": False,
        "uses_params_index": False,
        "uses_http_get": False,
        "uses_http_post": False,
        "uses_get_secret": False,
        "imports_jarvis_runtime": False,
        "forbidden_imports": [],
        "forbidden_calls": [],
    }

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return info

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == "jarvis_runtime":
                    info["imports_jarvis_runtime"] = True
                if n.name in ("requests", "config"):
                    info["forbidden_imports"].append(n.name)

        if isinstance(node, ast.ImportFrom):
            if node.module == "jarvis_runtime":
                info["imports_jarvis_runtime"] = True
            if node.module in ("requests", "config"):
                info["forbidden_imports"].append(f"from {node.module}")

        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__PROGRAM__":
                    info["has_program"] = True

        if isinstance(node, ast.FunctionDef) and node.name == "run":
            info["has_run"] = True
            for sub in ast.walk(node):
                if isinstance(sub, ast.Try):
                    info["run_has_try"] = True
                if isinstance(sub, ast.Return):
                    info["run_has_return"] = True
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                    if isinstance(sub.func.value, ast.Name) and sub.func.value.id == "params" and sub.func.attr == "get":
                        info["uses_params_get"] = True
                if isinstance(sub, ast.Subscript) and isinstance(sub.value, ast.Name) and sub.value.id == "params":
                    info["uses_params_index"] = True
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                    if isinstance(sub.func.value, ast.Name) and sub.func.value.id == "jarvis_runtime":
                        if sub.func.attr == "http_get_json":
                            info["uses_http_get"] = True
                        if sub.func.attr == "http_post_json":
                            info["uses_http_post"] = True
                        if sub.func.attr == "get_secret":
                            info["uses_get_secret"] = True

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "open":
                info["forbidden_calls"].append("open")

    return info

def run_tests(mod: Any) -> List[TestResult]:
    tests: Any = getattr(mod, "__TESTS__", None)
    results: List[TestResult] = []

    if tests is None:
        return results
    if not isinstance(tests, list):
        return [TestResult(name="__TESTS__", ok=False, error="__TESTS__ must be a list")]

    for i, t in enumerate(tests):
        name = f"test_{i}"
        if isinstance(t, dict) and isinstance(t.get("name"), str):
            name = t["name"]
        if not isinstance(t, dict):
            results.append(TestResult(name=name, ok=False, error="test case must be a dict"))
            continue

        params = t.get("params", {})
        expect_contains = t.get("expect_contains", [])
        expect_regex = t.get("expect_regex")
        expect_type = t.get("expect_type")
        mock_secrets = t.get("mock_secrets")
        mock_http_get = t.get("mock_http_get_json")
        mock_http_post = t.get("mock_http_post_json")

        if not isinstance(params, dict):
            results.append(TestResult(name=name, ok=False, error="params must be dict"))
            continue

        try:
            with _patched_runtime(
                mock_secrets=mock_secrets if isinstance(mock_secrets, dict) else None,
                mock_http_get=mock_http_get,
                mock_http_post=mock_http_post,
            ):
                out = mod.run(params)  # type: ignore

            if expect_type == "str" and not isinstance(out, str):
                raise AssertionError(f"Expected str output, got {type(out).__name__}")
            if expect_type == "dict[str,str]" and not _is_dict_str_str(out):
                raise AssertionError("Expected dict[str,str] output")

            out_s = out if isinstance(out, str) else str(out)

            if isinstance(expect_contains, list):
                for s in expect_contains:
                    if isinstance(s, str) and s not in out_s:
                        raise AssertionError(f"Missing substring: {s}")

            if isinstance(expect_regex, str):
                if not re.search(expect_regex, out_s):
                    raise AssertionError(f"Regex not matched: {expect_regex}")

            results.append(TestResult(name=name, ok=True, details={"output_preview": out_s[:200]}))
        except Exception as e:
            results.append(TestResult(name=name, ok=False, error=str(e), details={"trace": traceback.format_exc()}))

    return results

def _score(meta: Dict[str, Any], ast_info: Dict[str, Any], tests: List[TestResult], errors: List[str], warnings: List[str]) -> Tuple[int, Dict[str, Any]]:
    # Categories:
    # schema 30, stability 30, output 25, extensibility 15 = 100
    schema = 0
    stability = 0
    output = 0
    extensibility = 0

    params = meta.get("params", None)

    # --- Schema (30) ---
    if isinstance(params, list):
        schema += 5
        if len(params) <= 5:
            schema += 5
        else:
            schema += 2
            warnings.append("params count is high; planner/composability may worsen.")
        all_dict = all(isinstance(x, dict) for x in params)
        if all_dict:
            schema += 5
        missing_keys = 0
        placeholder_ok = 0
        api_key_bad = 0
        for item in params if isinstance(params, list) else []:
            if not isinstance(item, dict):
                continue
            if not all(k in item for k in _PARAM_REQUIRED_KEYS):
                missing_keys += 1
            key = item.get("key")
            if isinstance(key, str) and "api_key" in key.lower():
                api_key_bad += 1
            ph = item.get("placeholder")
            if isinstance(ph, str) and ph.strip():
                placeholder_ok += 1
        if missing_keys == 0 and len(params) > 0:
            schema += 10
        elif len(params) == 0:
            schema += 10  # empty params is fine
        else:
            schema += max(0, 10 - 2 * missing_keys)

        if len(params) > 0:
            schema += min(5, int((placeholder_ok / max(1, len(params))) * 5))
        else:
            schema += 5  # nothing to input -> OK

        if api_key_bad > 0:
            schema = max(0, schema - 10)
    else:
        # already an error, but keep score
        schema += 0

    # --- Stability (30) ---
    if ast_info.get("has_run"):
        stability += 10
    if ast_info.get("run_has_try"):
        stability += 10
    # params access style
    if ast_info.get("uses_params_get") or (not ast_info.get("uses_params_index")):
        stability += 10
    else:
        stability += 4
        warnings.append("run() uses params['x'] indexing; consider params.get(...) or clearer checks for robustness.")

    # --- Output (25) ---
    if ast_info.get("run_has_return"):
        output += 10
    # tests quality
    if len(tests) >= 1:
        output += 5
    passed = sum(1 for t in tests if t.ok)
    if len(tests) == 0:
        output += 0
    else:
        ratio = passed / max(1, len(tests))
        output += int(ratio * 10)  # up to 10

    # output preview sanity (if any passed)
    if passed > 0:
        output += 5
    else:
        output += 0

    # --- Extensibility (15) ---
    # forbidden imports/calls reduce
    if not ast_info.get("forbidden_imports") and not ast_info.get("forbidden_calls"):
        extensibility += 5
    else:
        warnings.append("Found forbidden imports/calls; portability/safety reduced.")
    # jarvis_runtime import usage
    if ast_info.get("imports_jarvis_runtime"):
        extensibility += 5
    # deterministic tests w/ mocks when needed
    needs_http = ast_info.get("uses_http_get") or ast_info.get("uses_http_post")
    needs_secret = ast_info.get("uses_get_secret")

    has_http_mock = any(isinstance(getattr_case, dict) and ("mock_http_get_json" in getattr_case or "mock_http_post_json" in getattr_case)
                        for getattr_case in getattr(meta, "__dummy__", []) )  # unreachable, kept simple

    # Instead, check test dict keys by reflecting raw tests via mod is not here.
    # We'll infer from TestResult details. If test executed without network/secrets it likely had mocks.
    # Give partial credit if tests exist.
    if len(tests) >= 1:
        extensibility += 5 if (needs_http or needs_secret) else 3

    total = schema + stability + output + extensibility

    # clamp
    total = max(0, min(100, int(total)))

    breakdown = {
        "schema": {"score": schema, "max": 30},
        "stability": {"score": stability, "max": 30},
        "output": {"score": output, "max": 25, "tests_passed": passed, "tests_total": len(tests)},
        "extensibility": {"score": extensibility, "max": 15},
    }

    # If there are hard errors, cap score to make it obvious
    if errors:
        total = min(total, 59)
        breakdown["note"] = "Hard errors present -> score capped"

    return total, breakdown

def gate(code: str) -> GateResult:
    errors: List[str] = []
    warnings: List[str] = []

    ast_info = _analyze_ast(code)

    # hard forbidden signals (safety)
    if ast_info.get("forbidden_imports"):
        errors.append(f"Forbidden import(s): {ast_info['forbidden_imports']}")
    if ast_info.get("forbidden_calls"):
        errors.append(f"Forbidden call(s): {ast_info['forbidden_calls']}")

    try:
        mod = load_module_from_code(code)
    except Exception as e:
        return GateResult(ok=False, errors=[f"Import/Load failed: {e}"], warnings=[], tests=[], score=0, score_breakdown={"note": "load failed"})

    meta = getattr(mod, "__PROGRAM__", None)
    meta_dict, meta_errors, meta_warnings = _validate_program_meta(meta)
    errors.extend(meta_errors)
    warnings.extend(meta_warnings)

    if not hasattr(mod, "run") or not callable(getattr(mod, "run")):
        errors.append("run(params) function missing or not callable")

    tests = run_tests(mod)
    for tr in tests:
        if not tr.ok:
            errors.append(f"Test failed: {tr.name}: {tr.error}")

    score, breakdown = _score(meta_dict, ast_info, tests, errors, warnings)

    return GateResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        tests=tests,
        score=score,
        score_breakdown=breakdown,
    )
