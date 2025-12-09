# ai_codegen.py (Jarvis v2 完全文)

import os, re, time, ast
from typing import Optional, List, Tuple, Any
from openai import OpenAI

_client: Optional[OpenAI] = None

def _client_singleton() -> OpenAI:
    global _client
    if _client is None:
        from config import OPENAI_API_KEY
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.S|re.I)
    return m.group(1).strip() if m else text.strip()

# ===========================
# Jarvis v2 SYSTEM プロンプト
# ===========================
SYSTEM = (
    "You are a Python PROGRAM generator.\n"
    "Your output MUST be a single, complete Python module.\n"
    "Do not output markdown, explanations, or comments outside the code.\n"
    "\n"
    "Requirements for generated modules:\n"
    "1) Must define __PROGRAM__ = {name:str, version:str, description:str, params:list, kind:str(optional)}\n"
    "2) params is a list of field schemas:\n"
    "   {\"key\":str, \"label\":str, \"type\":str, \"required\":bool, \"default\":any(optional), "
    "\"choices\": list(optional), \"placeholder\": str(optional)}\n"
    "3) Supported types: int, float, str, bool, select, list[int], list[float], list[str]\n"
    "4) Must define run(params: dict) -> str OR Dict[str,str]\n"
    "\n"
    "========= NEW JARVIS v2 RULES =========\n"
    "File I/O and Web API access ARE allowed, but ONLY via the official helper functions:\n"
    "    from jarvis_runtime import read_text, write_text, read_json, write_json,\n"
    "                               call_program_by_index, call_program_by_name,\n"
    "                               http_get_json, http_post_json\n"
    "Direct use of open(), requests.get(), requests.post(), or OS-level features is FORBIDDEN.\n"
    "\n"
    "You MUST use these helpers for:\n"
    " - reading/writing files\n"
    " - accessing saved program data\n"
    " - calling other Jarvis programs\n"
    " - accessing the web\n"
    "\n"
    "If __PROGRAM__[\"kind\"] == \"project_generator\":\n"
    "    run(params) MUST return Dict[str,str] where each key is a file path and value is code.\n"
    "\n"
    "Add short docstrings, type hints, and ensure schema consistency.\n"
)

# ==============
# AST チェック
# ==============
def _get_literal_dict(node: ast.AST) -> Optional[dict]:
    if not isinstance(node, ast.Dict):
        return None
    result = {}
    for k, v in zip(node.keys, node.values):
        if isinstance(k, ast.Str):
            key = k.s
        elif isinstance(k, ast.Constant):
            key = k.value
        else:
            return None

        if isinstance(v, ast.Constant):
            val = v.value
        elif isinstance(v, ast.Str):
            val = v.s
        elif isinstance(v, ast.List):
            lst = []
            for e in v.elts:
                if isinstance(e, ast.Constant):
                    lst.append(e.value)
                elif isinstance(e, ast.Str):
                    lst.append(e.s)
                elif isinstance(e, ast.Dict):
                    sub = _get_literal_dict(e)
                    if sub is None:
                        return None
                    lst.append(sub)
                else:
                    return None
            val = lst
        elif isinstance(v, ast.Dict):
            sub = _get_literal_dict(v)
            if sub is None:
                return None
            val = sub
        else:
            return None
        result[key] = val
    return result

def _score_and_validate(code: str) -> Tuple[int, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return (-10**9, str(e))

    has_meta = False
    has_run = False
    imports = 0
    funcs_typed = 0
    docstrings = 0
    has_params = False

    program_dict = None

    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "__PROGRAM__":
                    has_meta = True
                    if isinstance(n.value, ast.Dict):
                        program_dict = _get_literal_dict(n.value)

        if isinstance(n, ast.FunctionDef):
            if n.name == "run":
                has_run = True
            if n.returns:
                funcs_typed += 1
            if ast.get_docstring(n):
                docstrings += 1

        if isinstance(n, (ast.Import, ast.ImportFrom)):
            imports += 1

    if program_dict and "params" in program_dict:
        has_params = True
    else:
        return (-10**8, "params missing")

    score = 0
    if has_meta: score += 20
    if has_run: score += 20
    score += funcs_typed * 4
    score += docstrings * 2
    score -= max(0, imports - 10)

    return (score, "")

# ================================
# LLM 呼び出し（v2 用）
# ================================
def generate_program_best(spec: str, n: int = 2, retries: int = 2, model: Optional[str] = None) -> str:
    client = _client_singleton()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = (
        "Please generate a Python module that satisfies the Jarvis v2 rules.\n"
        "User request:\n" + spec + "\n"
    )

    def one():
        res = client.responses.create(
            model=model,
            instructions=SYSTEM,
            input=prompt,
            temperature=0.2,
            max_output_tokens=2000
        )
        return _extract_code(res.output_text)

    best = None
    best_score = -10**18

    for _ in range(retries):
        for __ in range(n):
            c = one()
            s, _err = _score_and_validate(c)
            if s > best_score:
                best_score = s
                best = c

    return best
