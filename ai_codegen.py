# ai_codegen.py (Jarvis v2.2 APIキー自動取得対応版)

import os, re, ast
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

# ===========================
# Jarvis v2.2 SYSTEM プロンプト
# ===========================
SYSTEM = (
    "You are Jarvis, a self-extensible Python program generator.\n"
    "Your output MUST be a single, complete Python module.\n"
    "Do NOT output markdown, explanations, or comments outside the code.\n\n"

    "================ API KEY RULES (CRITICAL) ================\n"
    "When generating programs that use Web APIs:\n"
    "- NEVER request API keys via params.\n"
    "- ALWAYS import API keys from config.py.\n"
    "- Use predefined environment keys such as:\n"
    "  WEATHER_API_KEY, NEWS_API_KEY, GEODB_API_KEY, OPENAI_API_KEY\n"
    "- If the required API key is None, run(params) MUST return a clear error string.\n"
    "- NEVER hardcode API keys.\n\n"

    "================ PROGRAM STRUCTURE ================\n"
    "1) Must define __PROGRAM__ = {name, version, description, params[, kind]}\n"
    "2) params MUST NOT include API keys.\n"
    "3) run(params) MUST return a string (unless project_generator).\n"
    "4) Use jarvis_runtime helpers ONLY for I/O or Web access:\n"
    "   http_get_json, http_post_json, read_text, write_text\n"
    "5) Direct use of requests, open(), os.system() is FORBIDDEN.\n\n"

    "================ STYLE ================\n"
    "- Add short docstrings and type hints.\n"
    "- Ensure schema consistency.\n"
    "- Output ONLY valid Python code.\n"
)

# ==========================
# AST 最低限チェック
# ==========================
def _get_literal_dict(node: ast.AST) -> Optional[dict]:
    if not isinstance(node, ast.Dict):
        return None
    result = {}
    for k, v in zip(node.keys, node.values):
        if isinstance(k, ast.Constant):
            key = k.value
        else:
            return None

        if isinstance(v, ast.Constant):
            val = v.value
        elif isinstance(v, ast.List):
            val = [e.value for e in v.elts if isinstance(e, ast.Constant)]
        elif isinstance(v, ast.Dict):
            val = _get_literal_dict(v)
        else:
            return None
        result[key] = val
    return result

def _score_and_validate(code: str) -> Tuple[int, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return (-10**9, str(e))

    score = 0
    has_program = False
    has_run = False
    imports_config = False
    bad_api_param = False

    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "__PROGRAM__":
                    has_program = True

        if isinstance(n, ast.FunctionDef) and n.name == "run":
            has_run = True

        if isinstance(n, ast.ImportFrom):
            if n.module == "config":
                imports_config = True

        if isinstance(n, ast.Str):
            if "api key" in n.s.lower():
                bad_api_param = True

    if not has_program:
        return (-10**8, "__PROGRAM__ missing")
    if not has_run:
        return (-10**8, "run() missing")
    if bad_api_param:
        return (-10**7, "API key requested via params")

    if imports_config:
        score += 50

    score += 20
    return (score, "")

# ==========================
# LLM 呼び出し
# ==========================
def generate_program_best(
    spec: str,
    n: int = 2,
    retries: int = 2,
    model: Optional[str] = None
) -> str:
    client = _client_singleton()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = (
        "Generate a Python program following Jarvis v2.2 rules.\n"
        "User request:\n" + spec
    )

    best = None
    best_score = -10**18

    for _ in range(retries):
        for __ in range(n):
            res = client.responses.create(
                model=model,
                instructions=SYSTEM,
                input=prompt,
                temperature=0.2,
                max_output_tokens=2200
            )
            code = _extract_code(res.output_text)
            score, _ = _score_and_validate(code)
            if score > best_score:
                best_score = score
                best = code

    return best or ""
