# ai_codegen.py
# Jarvis v2.6 - strict: params schema, no api_key in params, must import jarvis_runtime, must include __TESTS__

import os
import re
import ast
from typing import Optional, Tuple
from openai import OpenAI

_client: Optional[OpenAI] = None


def _client_singleton() -> OpenAI:
    global _client
    if _client is None:
        from config import OPENAI_API_KEY
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.S | re.I)
    return m.group(1).strip() if m else text.strip()


SYSTEM = (
    "You are a Python PROGRAM generator for a self-extensible AI framework called Jarvis.\n"
    "Return ONLY a complete Python module (no markdown, no commentary).\n"
    "\n"
    "=== HARD REQUIREMENTS ===\n"
    "\n"
    "0) You MUST include `import jarvis_runtime` near the top of the module.\n"
    "\n"
    "1) You MUST define __PROGRAM__ as a dict with:\n"
    "   - name: str\n"
    "   - version: str\n"
    "   - description: str\n"
    "   - params: list (REQUIRED)\n"
    "   - kind: str (optional)\n"
    "\n"
    "2) __PROGRAM__['params'] MUST be a LIST.\n"
    "   - If no input is needed, params MUST be [].\n"
    "   - Otherwise, params MUST be a list of schema dicts.\n"
    "   - NEVER put strings or explanations into params.\n"
    "\n"
    "   Each schema dict MUST include:\n"
    "     key: str\n"
    "     type: str\n"
    "     required: bool\n"
    "   It MAY include label/default/choices/placeholder.\n"
    "   IMPORTANT: Provide placeholder for each input whenever possible.\n"
    "\n"
    "3) You MUST define run(params: dict).\n"
    "   - run(params) MUST be deterministic and self-contained.\n"
    "   - It MUST rely ONLY on params and jarvis_runtime.\n"
    "\n"
    "4) Secrets / API keys:\n"
    "   - You MUST NOT ask the user to input API keys.\n"
    "   - You MUST NOT include api_key in params.\n"
    "   - If a secret is needed, obtain it ONLY via jarvis_runtime.get_secret('NAME').\n"
    "   - NEVER read workspace/secrets via read_text/read_json.\n"
    "\n"
    "5) Web access:\n"
    "   - Do NOT import requests.\n"
    "   - Use jarvis_runtime.http_get_json / http_post_json only.\n"
    "\n"
    "6) File I/O:\n"
    "   - Do NOT use open(). Use jarvis_runtime.read_text/write_text/read_json/write_json.\n"
    "\n"
    "7) Tests (REQUIRED):\n"
    "   - Include __TESTS__ as a list of test case dicts.\n"
    "   - Each test case MUST include 'params'.\n"
    "   - If your code calls jarvis_runtime.http_get_json, include 'mock_http_get_json' in tests.\n"
    "   - If your code calls jarvis_runtime.http_post_json, include 'mock_http_post_json' in tests.\n"
    "   - If your code calls jarvis_runtime.get_secret, include 'mock_secrets' in tests.\n"
    "   - Keep tests offline and deterministic.\n"
    "\n"
    "8) Output must be valid Python code only.\n"
)

FORBIDDEN_IMPORTS = {"requests", "config"}
FORBIDDEN_BUILTIN_CALLS = {"open"}
FORBIDDEN_STRINGS = {"your_api_key", "api_key_here"}
_PARAM_REQUIRED_KEYS = {"key", "type", "required"}


def _const_str(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _has_import_jarvis_runtime(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == "jarvis_runtime":
                    return True
        # NOTE: "from jarvis_runtime import X" は jarvis_runtime 名が使えない可能性があるので、
        # ここでは import jarvis_runtime を強制する（より安全）
    return False


def _uses_jarvis_runtime_name(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "jarvis_runtime":
            return True
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "jarvis_runtime":
            return True
    return False


def _validate_program_params_dict(node: ast.Dict) -> Optional[str]:
    for k, v in zip(node.keys, node.values):
        ks = _const_str(k)
        if ks == "params":
            if not isinstance(v, ast.List):
                return "params must be a list"
            for elt in v.elts:
                if not isinstance(elt, ast.Dict):
                    return "params items must be dicts"
                found = set()
                for kk in elt.keys:
                    kks = _const_str(kk)
                    if kks:
                        found.add(kks)
                missing = _PARAM_REQUIRED_KEYS - found
                if missing:
                    return f"param schema missing keys: {sorted(missing)}"
                for kk, vv in zip(elt.keys, elt.values):
                    if _const_str(kk) == "key":
                        keyname = _const_str(vv)
                        if keyname and "api_key" in keyname.lower():
                            return "api_key must not be included in params"
            return None
    return "__PROGRAM__ must include 'params'"


def _validate_no_secrets_read(tree: ast.AST) -> Optional[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "jarvis_runtime" and node.func.attr in ("read_text", "read_json"):
                    if node.args:
                        s = _const_str(node.args[0])
                        if s and ("secrets/" in s or s.startswith("secrets")):
                            return "Do not read secrets via read_text/read_json; use get_secret()"
    return None


def _validate_tests_present(tree: ast.AST) -> Optional[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__TESTS__":
                    if not isinstance(node.value, ast.List):
                        return "__TESTS__ must be a list"
                    for elt in node.value.elts:
                        if not isinstance(elt, ast.Dict):
                            return "__TESTS__ items must be dicts"
                        keys = set(_const_str(k) for k in elt.keys if _const_str(k))
                        if "params" not in keys:
                            return "__TESTS__ each item must include 'params'"
                    return None
    return "__TESTS__ missing (tests are required)"


def _score_and_validate(code: str) -> Tuple[int, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return (-10**9, f"SyntaxError: {e}")

    has_program = False
    has_run = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name in FORBIDDEN_IMPORTS:
                    return (-10**8, f"Forbidden import: {n.name}")
        if isinstance(node, ast.ImportFrom):
            if node.module in FORBIDDEN_IMPORTS:
                return (-10**8, f"Forbidden import: from {node.module} import ...")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_BUILTIN_CALLS:
                return (-10**8, f"Forbidden call: {node.func.id}")

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in FORBIDDEN_STRINGS:
                return (-10**8, "Forbidden placeholder string used")

        if isinstance(node, ast.FunctionDef) and node.name == "run":
            has_run = True

        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__PROGRAM__":
                    has_program = True
                    if isinstance(node.value, ast.Dict):
                        err = _validate_program_params_dict(node.value)
                        if err:
                            return (-10**8, err)
                    else:
                        return (-10**8, "__PROGRAM__ must be a dict")

    if not has_program:
        return (-10**8, "__PROGRAM__ missing")
    if not has_run:
        return (-10**8, "run() missing")

    # NEW: must import jarvis_runtime (hard requirement)
    if not _has_import_jarvis_runtime(tree):
        return (-10**8, "Missing required `import jarvis_runtime`")

    # If jarvis_runtime is referenced, ensure import exists (double safety)
    if _uses_jarvis_runtime_name(tree) and not _has_import_jarvis_runtime(tree):
        return (-10**8, "jarvis_runtime is referenced but not imported")

    err = _validate_no_secrets_read(tree)
    if err:
        return (-10**8, err)

    err = _validate_tests_present(tree)
    if err:
        return (-10**8, err)

    return (100, "")


def generate_program_best(
    spec: str,
    n: int = 2,
    retries: int = 2,
    model: Optional[str] = None
) -> str:
    client = _client_singleton()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = (
        "Generate a Python program following Jarvis rules.\n"
        "User request:\n" + spec
    )

    best_code: Optional[str] = None
    best_score = -10**18
    best_err = ""

    for _ in range(retries):
        for __ in range(n):
            res = client.responses.create(
                model=model,
                instructions=SYSTEM,
                input=prompt,
                temperature=0.2,
                max_output_tokens=2400
            )
            code = _extract_code(res.output_text)
            score, err = _score_and_validate(code)
            if score > best_score:
                best_score = score
                best_code = code
                best_err = err
            if score >= 100:
                return code

    raise RuntimeError(f"Failed to generate a valid program: {best_err}")
