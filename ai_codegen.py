# ai_codegen.py
# Jarvis v2.4
# - 生成コードは「import jarvis_runtime」を必須
# - secrets/APIキーを params に出さない（jarvis_runtime.get_secret を使わせる）
# - 実行前品質ゲートで落ちるコードを減らすための軽いASTチェック付き

from __future__ import annotations

import os
import re
import ast
from typing import Optional, Tuple

from openai import OpenAI

# -----------------------
# OpenAI client singleton
# -----------------------
_client: Optional[OpenAI] = None


def _client_singleton() -> OpenAI:
    global _client
    if _client is None:
        from config import OPENAI_API_KEY  # OpenAI用だけは config.py でOK（GitHubに上げない運用）
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


# -----------------------
# Utility
# -----------------------
def _extract_code(text: str) -> str:
    """Extract fenced python code if present; otherwise return raw text."""
    m = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.S | re.I)
    return m.group(1).strip() if m else text.strip()


# =======================
# Jarvis SYSTEM PROMPT
# =======================
SYSTEM = (
    "You are a Python PROGRAM generator for a self-extensible AI framework called Jarvis.\n"
    "Return ONLY a complete Python module (no markdown, no commentary).\n"
    "\n"
    "=== HARD REQUIREMENTS ===\n"
    "1) You MUST define __PROGRAM__ as a dict with:\n"
    "   - name: str\n"
    "   - version: str\n"
    "   - description: str\n"
    "   - params: list (REQUIRED)\n"
    "   - kind: str (optional)\n"
    "\n"
    "2) __PROGRAM__['params'] MUST be a LIST of schema dicts describing ONLY inputs required by THIS program.\n"
    "   If no inputs are needed, params MUST be an empty list.\n"
    "   Each schema dict MUST be:\n"
    "     {\"key\": str, \"label\": str, \"type\": str, \"required\": bool,\n"
    "      \"default\": any (optional), \"choices\": list (optional), \"placeholder\": str (optional)}\n"
    "   Supported types: int, float, str, bool, select, list[int], list[float], list[str].\n"
    "\n"
    "3) You MUST define run(params: dict).\n"
    "   - run(params) must be self-contained.\n"
    "   - It must rely ONLY on params and the jarvis_runtime module.\n"
    "\n"
    "4) Do NOT put secrets/API keys in params.\n"
    "   Do NOT create params like api_key/token/secret/key.\n"
    "   If a secret is needed, use jarvis_runtime.get_secret(\"SOME_KEY\").\n"
    "\n"
    "5) You MUST include exactly: `import jarvis_runtime` near the top.\n"
    "   Do NOT use `from jarvis_runtime import ...`.\n"
    "\n"
    "6) For web access, use jarvis_runtime.http_get_json / http_post_json / http_post_form only.\n"
    "   Do NOT import/use requests. Do NOT use jarvis_runtime.fetch.\n"
    "   If the request is translation, you MUST call jarvis_runtime.translate_text(text, target_lang[, source_lang]).\n"
    "   Do NOT pass any API key argument. translate_text reads ./workspace/secrets/DEEPL_API_KEY.txt internally.\n"
    "   MUST NOT use OpenAI for translation.\n"


    "7) For file I/O, use jarvis_runtime.read_text/write_text/read_json/write_json only.\n"
    "   Do NOT use open().\n"
    "\n"
    "8) If kind is specified:  \n"
    "   - module (default): run returns a string\n"
    "   - project_generator: run returns Dict[str,str] mapping file paths to file contents\n"
    "   project_generator must NOT write files directly.\n"
    "\n"
    "9) The output MUST be valid Python code ONLY.\n"
)


# =======================
# Light AST validation (selection)
# =======================
FORBIDDEN_STRINGS = {"your_api_key", "api_key_here"}


def _score_and_validate(code: str) -> Tuple[int, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return (-10**9, f"SyntaxError: {e}")

    has_program = False
    has_run = False
    has_import_runtime = False
    has_from_import_runtime = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__PROGRAM__":
                    has_program = True

        if isinstance(node, ast.FunctionDef) and node.name == "run":
            has_run = True

        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == "jarvis_runtime":
                    has_import_runtime = True

        if isinstance(node, ast.ImportFrom) and node.module == "jarvis_runtime":
            has_from_import_runtime = True

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in FORBIDDEN_STRINGS:
                return (-10**8, "Forbidden fallback secret string used")

        # forbid jarvis_runtime.fetch
        if isinstance(node, ast.Attribute) and node.attr == "fetch":
            if isinstance(node.value, ast.Name) and node.value.id == "jarvis_runtime":
                return (-10**8, "Forbidden call: jarvis_runtime.fetch")

    if not has_program:
        return (-10**8, "__PROGRAM__ missing")
    if not has_run:
        return (-10**8, "run() missing")
    if has_from_import_runtime:
        return (-10**8, "Do not use `from jarvis_runtime import ...`; use `import jarvis_runtime`")
    if not has_import_runtime:
        return (-10**8, "`import jarvis_runtime` missing")

    return (100, "")


# =======================
# Program generation
# =======================
def generate_program_best(
    spec: str,
    n: int = 2,
    retries: int = 2,
    model: Optional[str] = None,
) -> str:
    client = _client_singleton()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = "Generate a Python program for Jarvis.\nUser request:\n" + spec

    best_code: Optional[str] = None
    best_score = -10**18

    for _ in range(retries):
        for __ in range(n):
            res = client.responses.create(
                model=model,
                instructions=SYSTEM,
                input=prompt,
                temperature=0.2,
                max_output_tokens=2200,
            )
            code = _extract_code(res.output_text)
            score, _err = _score_and_validate(code)
            if score > best_score:
                best_score = score
                best_code = code

    return best_code or ""
