# ai_codegen.py
# Jarvis v2.3 - APIキーを必ず config.py から拾わせる強制設計版

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
        from config import OPENAI_API_KEY
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

# -----------------------
# Utility
# -----------------------
def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.S | re.I)
    return m.group(1).strip() if m else text.strip()

# =======================
# Jarvis SYSTEM PROMPT
# =======================
SYSTEM = (
    "You are a Python PROGRAM generator for a self-extensible AI framework called Jarvis.\n"
    "Return ONLY a complete Python module (no markdown, no commentary).\n"
    "\n"
    "Your task is to generate a single Python module that can be safely executed "
    "inside the Jarvis framework.\n"
    "\n"
    "=== HARD REQUIREMENTS ===\n"
    "\n"
    "1. You MUST define __PROGRAM__ as a dictionary with the following fields:\n"
    "   - name: str\n"
    "   - version: str\n"
    "   - description: str\n"
    "   - params: list (REQUIRED)\n"
    "   - kind: str (optional)\n"
    "\n"
    "2. The 'params' field in __PROGRAM__ MUST be a LIST of schema objects.\n"
    "   Do NOT use dict-style params definitions.\n"
    "\n"
    "   Each params schema object MUST follow this structure:\n"
    "   {\n"
    "     \"key\": str,\n"
    "     \"label\": str,\n"
    "     \"type\": str,\n"
    "     \"required\": bool,\n"
    "     \"default\": any (optional),\n"
    "     \"choices\": list (optional),\n"
    "     \"placeholder\": str (optional)\n"
    "   }\n"
    "\n"
    "   Supported types are:\n"
    "   - \"int\", \"float\", \"str\", \"bool\", \"select\",\n"
    "   - \"list[int]\", \"list[float]\", \"list[str]\".\n"
    "\n"
    "   Example of a CORRECT params schema:\n"
    "   __PROGRAM__ = {\n"
    "     \"params\": [\n"
    "       {\n"
    "         \"key\": \"city\",\n"
    "         \"label\": \"City Name\",\n"
    "         \"type\": \"str\",\n"
    "         \"required\": True,\n"
    "         \"placeholder\": \"Tokyo\"\n"
    "       }\n"
    "     ]\n"
    "   }\n"
    "\n"
    "3. You MUST define a function:\n"
    "     run(params: dict)\n"
    "\n"
    "   - run(params) MUST be self-contained.\n"
    "   - It MUST rely ONLY on the provided params and the 'jarvis_runtime' module.\n"
    "   - It MUST NOT depend on global variables, environment state, or external configuration files.\n"
    "\n"
    "4. You MUST NOT import or read secrets or API keys from config.py.\n"
    "   Secrets such as API keys MUST be provided either:\n"
    "   - explicitly via params, OR\n"
    "   - via files under the './workspace' directory using jarvis_runtime.read_text or read_json.\n"
    "\n"
    "   Prefer passing API keys explicitly via params unless instructed otherwise.\n"
    "\n"
    "5. When accessing external web APIs:\n"
    "   - You MUST NOT import or use 'requests' directly.\n"
    "   - You MUST ALWAYS use helper functions from 'jarvis_runtime':\n"
    "       - http_get_json\n"
    "       - http_post_json\n"
    "\n"
    "6. Any file I/O, tool-to-tool invocation, or web access MUST go through 'jarvis_runtime'.\n"
    "   Direct usage of open(), requests, or registry functions is considered a violation.\n"
    "\n"
    "   Allowed helpers from jarvis_runtime include (but are not limited to):\n"
    "   - read_text, write_text\n"
    "   - read_json, write_json\n"
    "   - call_program_by_index, call_program_by_name\n"
    "   - http_get_json, http_post_json\n"
    "\n"
    "7. If __PROGRAM__[\"kind\"] is specified:\n"
    "   - \"module\" (default): run(params) returns a string result\n"
    "   - \"project_generator\": run(params) returns Dict[str, str]\n"
    "     mapping file paths to file contents.\n"
    "\n"
    "   For project_generator:\n"
    "   - DO NOT write files directly.\n"
    "   - ONLY return the mapping of file paths to source code strings.\n"
    "\n"
    "8. The generated code MUST:\n"
    "   - Include type hints where appropriate\n"
    "   - Include concise docstrings\n"
    "   - Handle edge cases (missing params, empty input, None values)\n"
    "   - Avoid unnecessary imports\n"
    "   - Be deterministic and readable\n"
    "\n"
    "9. The output MUST be valid Python code ONLY.\n"
    "   Do NOT include explanations, comments outside the code, or markdown.\n"
)


# =======================
# AST validation (核心)
# =======================
FORBIDDEN_STRINGS = {
    "your_api_key",
    "api_key_here",
}

FORBIDDEN_CALLS = {
    "read_json",
}

def _score_and_validate(code: str) -> Tuple[int, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return (-10**9, f"SyntaxError: {e}")

    has_program = False
    has_run = False
    imported_config_key = False

    # APIキー名の正規表現
    api_key_pattern = re.compile(r".*_API_KEY$")

    for node in ast.walk(tree):
        # __PROGRAM__ の存在
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__PROGRAM__":
                    has_program = True

        # run 関数
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            has_run = True

        # config.py からの import チェック
        if isinstance(node, ast.ImportFrom) and node.module == "config":
            for n in node.names:
                if api_key_pattern.match(n.name):
                    imported_config_key = True

        # 禁止文字列チェック
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in FORBIDDEN_STRINGS:
                return (-10**8, "Forbidden API key fallback string used")

        # 禁止関数呼び出し
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    return (-10**8, f"Forbidden call: {node.func.id}")

    if not has_program:
        return (-10**8, "__PROGRAM__ missing")
    if not has_run:
        return (-10**8, "run() missing")
    if not imported_config_key:
        return (-10**8, "API key not imported from config.py")

    # 合格
    score = 100
    return (score, "")

# =======================
# Program generation
# =======================
def generate_program_best(
    spec: str,
    n: int = 2,
    retries: int = 2,
    model: Optional[str] = None
) -> str:
    client = _client_singleton()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = (
        "Generate a Python program following Jarvis v2.3 rules.\n"
        "User request:\n" + spec
    )

    best_code = None
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
            score, err = _score_and_validate(code)
            if score > best_score:
                best_score = score
                best_code = code

    return best_code or ""
