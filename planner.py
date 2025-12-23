# planner.py
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import jarvis_runtime
from openai import OpenAI

from registry import list_programs, load_module_by_index


# -----------------------
# OpenAI client
# -----------------------
_client: Optional[OpenAI] = None


def _client_singleton() -> OpenAI:
    global _client
    if _client is None:
        from config import OPENAI_API_KEY
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


# -----------------------
# Helpers
# -----------------------
def _extract_json(text: str) -> str:
    # fenced json
    m = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S | re.I)
    if m:
        return m.group(1).strip()
    # try to find first {...}
    m = re.search(r"(\{.*\})", text, flags=re.S)
    return m.group(1).strip() if m else text.strip()


def _safe_str(x: Any) -> str:
    if isinstance(x, (dict, list)):
        return json.dumps(x, ensure_ascii=False, indent=2)
    return str(x)


def _get_tool_catalog() -> List[Dict[str, Any]]:
    """
    registry からツールのメタ情報を集める。
    壊れてるツールがあっても planner が落ちないようにスキップする。
    """
    catalog: List[Dict[str, Any]] = []
    progs = list_programs()

    for i, p in enumerate(progs):
        try:
            mod = load_module_by_index(i)
            meta = getattr(mod, "__PROGRAM__", None)
            if not isinstance(meta, dict):
                continue
            name = meta.get("name") or p.get("name") or f"program_{i}"
            desc = meta.get("description", "")
            params = meta.get("params", [])
            kind = meta.get("kind", "module") or "module"

            # params は list[dict] の前提。違ったら空扱いにする
            if not isinstance(params, list) or any(not isinstance(x, dict) for x in params):
                params = []

            # 小さく整形（LLMへ渡す情報量を抑える）
            slim_params = []
            for it in params:
                slim_params.append(
                    {
                        "key": it.get("key"),
                        "type": it.get("type"),
                        "required": it.get("required"),
                        "placeholder": it.get("placeholder", ""),
                        "label": it.get("label", it.get("key", "")),
                    }
                )

            catalog.append(
                {
                    "name": name,
                    "description": desc,
                    "params": slim_params,
                    "kind": kind,
                }
            )
        except Exception:
            # 1個壊れてても planner は動かす
            continue

    return catalog


def _prompt_missing_params(step_meta: Dict[str, Any], provided: Dict[str, Any]) -> Dict[str, Any]:
    """
    step_meta.params を見て、required のうち未指定/None を人間に聞く。
    """
    params_schema = step_meta.get("params", [])
    if not isinstance(params_schema, list):
        return provided

    out = dict(provided)
    for it in params_schema:
        if not isinstance(it, dict):
            continue
        key = it.get("key")
        if not isinstance(key, str) or not key:
            continue

        required = bool(it.get("required", False))
        typ = it.get("type", "str")
        label = it.get("label", key)
        placeholder = it.get("placeholder", "")

        if (key not in out) or (out.get(key) is None):
            if not required:
                continue

            hint = f"[{typ}]"
            if placeholder:
                hint += f" 例: {placeholder}"
            while True:
                v = input(f"- {label} {hint}\n  {key}> ").strip()
                if not v:
                    print("  必須です。入力してください。")
                    continue
                out[key] = v
                break

    return out


# -----------------------
# LLM planning
# -----------------------
PLANNER_SYSTEM = (
    "You are a planning module for Jarvis.\n"
    "You will be given a user goal and a catalog of available programs.\n"
    "Return ONLY JSON.\n\n"
    "Create a pipeline plan where each step calls one existing program.\n"
    "The output of a step may be used as input to a later step using the special string \"$prev\".\n"
    "If a required input cannot be inferred from the goal, set it to null and the runtime will ask the user.\n\n"
    "Output schema:\n"
    "{\n"
    "  \"steps\": [\n"
    "    {\"program\": \"EXACT_PROGRAM_NAME\", \"params\": {\"key\": \"value or $prev or null\"}}\n"
    "  ]\n"
    "}\n"
    "Rules:\n"
    "- Use ONLY program names from the catalog.\n"
    "- Keep steps <= 6.\n"
    "- Do NOT invent new tools.\n"
)


def _make_plan(goal: str, catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = _client_singleton()
    model = "gpt-4o-mini"

    prompt = (
        "GOAL:\n"
        f"{goal}\n\n"
        "CATALOG (available programs):\n"
        f"{json.dumps(catalog, ensure_ascii=False)}\n"
    )

    res = client.responses.create(
        model=model,
        instructions=PLANNER_SYSTEM,
        input=prompt,
        temperature=0.2,
        max_output_tokens=900,
    )

    raw = _extract_json(res.output_text)
    plan = json.loads(raw)

    if not isinstance(plan, dict) or "steps" not in plan:
        raise ValueError("Planner returned invalid JSON (missing steps)")
    if not isinstance(plan["steps"], list) or not plan["steps"]:
        raise ValueError("Planner returned empty steps")
    if len(plan["steps"]) > 6:
        plan["steps"] = plan["steps"][:6]
    return plan


# -----------------------
# Execute pipeline
# -----------------------
def plan_and_execute(goal: str) -> str:
    """
    メニュー7用：
    目標(goal) → プラン生成 → 足りない入力だけ聞く → パイプライン実行 → 最終結果を返す
    """
    catalog = _get_tool_catalog()
    if not catalog:
        return "[エラー] 登録済みプログラムがありません（合成する部品がない）"

    # name -> meta
    meta_by_name = {t["name"]: t for t in catalog}

    plan = _make_plan(goal, catalog)

    steps = plan.get("steps", [])
    if not isinstance(steps, list):
        return "[エラー] plan.steps が不正です"

    # プラン表示（見栄え & デバッグ）
    lines: List[str] = []
    lines.append("=== プラン（Pipeline） ===")
    for i, s in enumerate(steps):
        lines.append(f"{i+1}. {s.get('program')}  params={s.get('params')}")
    lines.append("==========================")
    print("\n".join(lines))

    ok = input("このプランで実行しますか？ (y/n): ").strip().lower()
    if ok != "y":
        return "キャンセルしました。"

    prev_out: str = ""
    trace: List[str] = []

    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            return f"[エラー] step_{idx} が辞書ではありません"

        prog_name = step.get("program")
        if not isinstance(prog_name, str) or prog_name not in meta_by_name:
            return f"[エラー] step_{idx} program が不正です: {prog_name}"

        params = step.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return f"[エラー] step_{idx} params が辞書ではありません"

        # $prev を置換
        resolved: Dict[str, Any] = {}
        for k, v in params.items():
            if isinstance(v, str) and v.strip() == "$prev":
                resolved[k] = prev_out
            else:
                resolved[k] = v

        # null/不足必須を聞く
        resolved = _prompt_missing_params(meta_by_name[prog_name], resolved)

        trace.append(f"\n--- step {idx+1}: {prog_name} ---")
        trace.append(f"params = {json.dumps(resolved, ensure_ascii=False)}")

        # 実行
        try:
            out = jarvis_runtime.call_program_by_name(prog_name, resolved)
        except Exception as e:
            trace.append(f"[ERROR] {e}")
            return "\n".join(trace)

        prev_out = _safe_str(out)
        trace.append("output =")
        trace.append(prev_out)

    trace.append("\n=== FINAL OUTPUT ===")
    trace.append(prev_out)
    return "\n".join(trace)
