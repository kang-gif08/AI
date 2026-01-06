from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Callable, Tuple, Optional

from ai_codegen import generate_program_best as generate_program
from quality_gate import gate, format_result, GateResult
from registry import (
    save_program,
    register_program,
    list_programs,
    run_program_by_index,
    read_program_source_by_index,
    overwrite_program_by_index,
    delete_program_by_index,
    load_module_by_index,
)

# ===============================
# 入力（params）
# ===============================
def prompt_params() -> Dict[str, Any]:
    """
    旧来の key=value 入力方式。
    値は JSON として解釈を試み、失敗したら文字列のまま扱う。
    """
    params: Dict[str, Any] = {}
    print("=== パラメータ入力（key=value） ===")
    print("空行で終了。例: city=Tokyo / limit=10 / flags=[1,2,3]")
    while True:
        line = input("> ").strip()
        if not line:
            break
        if "=" not in line:
            print("  形式が違います。key=value で入力してください。")
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        try:
            params[k] = json.loads(v)
        except Exception:
            params[k] = v
    return params


def _cast_bool(val: str) -> bool:
    return val.lower() in ("1", "true", "t", "yes", "y", "on")


def _parse_list(val: str, elem_cast: Callable[[str], Any]) -> List[Any]:
    if not val.strip():
        return []
    return [elem_cast(x.strip()) for x in val.split(",") if x.strip()]


def prompt_params_from_schema(schema: Any, prefill: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    __PROGRAM__['params'] を前提とした対話入力。
    - schema が壊れていても Jarvis 本体が落ちないように防御する
    - prefill がある場合、その key は入力をスキップしてそのまま使う（A→B 用）
    """
    if not isinstance(schema, list) or any(not isinstance(x, dict) for x in schema):
        print("[警告] スキーマが不正です（list[dict]ではありません）。key=value方式にフォールバックします。")
        base = prompt_params()
        if prefill:
            base.update(prefill)
        return base

    params: Dict[str, Any] = {}
    if prefill:
        params.update(prefill)

    print("=== パラメータ入力（スキーマ） ===")

    for item in schema:
        key = item.get("key")
        if not isinstance(key, str) or not key:
            print("[警告] スキーマ項目に key がありません。スキップします。")
            continue

        # prefill 済みは聞かない
        if key in params and params[key] is not None:
            continue

        label = item.get("label", key)
        typ = item.get("type", "str")
        required = bool(item.get("required", False))
        default = item.get("default", "")
        choices = item.get("choices")
        placeholder = item.get("placeholder", "")

        hint_parts: List[str] = [f"[{typ}]"]
        if choices and typ == "select":
            hint_parts.append(f"選択肢: {', '.join(map(str, choices))}")
        if isinstance(typ, str) and typ.startswith("list["):
            hint_parts.append("カンマ区切りで入力")
        if placeholder:
            hint_parts.append(f"例: {placeholder}")
        if default != "":
            hint_parts.append(f"default: {default}")
        if required:
            hint_parts.append("(required)")
        hint = " ".join(hint_parts)

        while True:
            val = input(f"- {label} {hint}\n  {key}> ").strip()

            if not val:
                if default != "":
                    val = str(default)
                elif required:
                    print("  必須です。入力してください。")
                    continue
                else:
                    params[key] = None
                    break

            try:
                casted: Any
                if typ == "int":
                    casted = int(val)
                elif typ == "float":
                    casted = float(val)
                elif typ == "bool":
                    casted = _cast_bool(val)
                elif typ == "select":
                    if not choices:
                        raise ValueError("select に choices がありません")
                    if val not in choices:
                        print(f"  無効です。{choices} から選んでください。")
                        continue
                    casted = val
                elif typ == "list[int]":
                    casted = _parse_list(val, int)
                elif typ == "list[float]":
                    casted = _parse_list(val, float)
                elif typ == "list[str]":
                    casted = _parse_list(val, str)
                else:
                    casted = val

                params[key] = casted
                break
            except Exception as e:
                print("  入力エラー:", e)

    return params


# ===============================
# 「作って」1回だけで
# 生成 -> 自己評価 -> 必要なら再生成（回数制限）を内部でやる
# ===============================
def _build_fix_spec(original_spec: str, code: str, gate_res: GateResult) -> str:
    return (
        "The previous program failed the quality gate. Fix ALL errors below and return the FULL corrected module.\n"
        "Return ONLY valid Python code. No markdown.\n\n"
        "=== Original user request ===\n"
        f"{original_spec}\n\n"
        "=== Quality gate errors ===\n"
        + "\n".join(f"- {e}" for e in gate_res.errors)
        + "\n\n=== Previous code ===\n"
        + code
    )


def generate_with_preflight(spec: str, max_regens: int = 2) -> Tuple[str, GateResult, int]:
    """
    人間は spec を1回入力するだけ。
    Jarvis内部で:
      生成 -> quality_gate -> (失敗なら) 自動再生成 を最大 max_regens 回まで
    """
    code = generate_program(spec)
    res = gate(code)

    regens = 0
    while (not res.ok) and regens < max_regens:
        regens += 1
        fix_spec = _build_fix_spec(spec, code, res)
        code = generate_program(fix_spec)
        res = gate(code)

    return code, res, regens


# ===============================
# UI
# ===============================
def menu() -> int:
    print("\n=== Self-Extensible Programs (Jarvis) ===")
    print("1) 新しいプログラムを生成して登録する（自己評価→必要なら再生成まで自動）")
    print("2) 登録済みプログラムを一覧表示する")
    print("3) 登録済みプログラムを実行する")
    print("4) 登録済みプログラムを編集する（自己評価→必要なら再生成まで自動）")
    print("5) 登録済みプログラムを削除する")
    print("6) A→B パイプライン合体（Aの出力をBへ渡す）")
    print("7) 終了")
    while True:
        sel = input("> 番号: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= 7:
            return int(sel)
        print("  無効な入力です。")


def looks_like_project_generator(out: Any) -> bool:
    """
    project_generator の返り値かどうかを安全に判定する。
    - Dict[str,str] っぽい時だけ True
    """
    if not isinstance(out, dict):
        return False
    if not out:
        return False
    for k, v in out.items():
        if not isinstance(k, str) or not isinstance(v, str):
            return False
        if len(k) > 2000 or len(v) > 2_000_000:
            return False
    return True


def _safe_str(x: Any) -> str:
    if isinstance(x, (dict, list)):
        try:
            return json.dumps(x, ensure_ascii=False, indent=2)
        except Exception:
            return str(x)
    return str(x)


def _get_schema_and_kind(idx: int) -> Tuple[Any, str]:
    schema = None
    kind = "module"
    try:
        mod = load_module_by_index(idx)
        prog = getattr(mod, "__PROGRAM__", {})
        if isinstance(prog, dict):
            schema = prog.get("params")
            kind = prog.get("kind", "module") or "module"
    except Exception:
        schema = None
        kind = "module"
    return schema, kind


def _infer_b_input_key(schema_b: Any) -> Optional[str]:
    """
    B の params から「Aの出力を入れそうなキー」を推測。
    1) required が1個ならそれ
    2) よくあるキー名を優先
    3) 無理なら None
    """
    if not isinstance(schema_b, list):
        return None
    items = [x for x in schema_b if isinstance(x, dict) and isinstance(x.get("key"), str) and x.get("key")]
    if not items:
        return None

    req = [x for x in items if bool(x.get("required", False))]
    if len(req) == 1:
        return str(req[0]["key"])

    prefer = [
        "input", "text", "query", "prompt", "content", "message",
        "keyword", "topic", "name", "city", "location"
    ]
    keymap = {str(x["key"]).lower(): str(x["key"]) for x in items}
    for p in prefer:
        if p in keymap:
            return keymap[p]
    return None


def _build_pipeline_wrapper_code(idx_a: int, idx_b: int, b_input_key: str) -> str:
    """
    A→B を新しいプログラムとして登録するためのラッパを生成（LLMなし）。
    - Aの params をそのまま受け取る
    - Bの params は b_ プレフィックスで受け取る（衝突回避）
    - Bの b_input_key は Aの出力を自動で入れる（ユーザーに聞かない）
    """
    mod_a = load_module_by_index(idx_a)
    mod_b = load_module_by_index(idx_b)
    prog_a = getattr(mod_a, "__PROGRAM__", {}) if isinstance(getattr(mod_a, "__PROGRAM__", None), dict) else {}
    prog_b = getattr(mod_b, "__PROGRAM__", {}) if isinstance(getattr(mod_b, "__PROGRAM__", None), dict) else {}

    name_a = str(prog_a.get("name", f"Program{idx_a}"))
    name_b = str(prog_b.get("name", f"Program{idx_b}"))

    schema_a = prog_a.get("params", [])
    schema_b = prog_b.get("params", [])

    def clean_item(it: Dict[str, Any], key_override: Optional[str] = None, label_prefix: str = "") -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "key": key_override if key_override else it.get("key"),
            "label": (label_prefix + (it.get("label") or it.get("key") or "")).strip(),
            "type": it.get("type", "str"),
            "required": bool(it.get("required", False)),
        }
        if "default" in it:
            out["default"] = it.get("default")
        if "choices" in it:
            out["choices"] = it.get("choices")
        if "placeholder" in it:
            out["placeholder"] = it.get("placeholder")
        return out

    params_all: List[Dict[str, Any]] = []

    if isinstance(schema_a, list):
        for it in schema_a:
            if isinstance(it, dict) and isinstance(it.get("key"), str) and it.get("key"):
                params_all.append(clean_item(it))

    if isinstance(schema_b, list):
        for it in schema_b:
            if not (isinstance(it, dict) and isinstance(it.get("key"), str) and it.get("key")):
                continue
            k = str(it["key"])
            if k == b_input_key:
                continue
            params_all.append(clean_item(it, key_override=f"b_{k}", label_prefix="B: "))

    wrapper = f"""import jarvis_runtime
import json

__PROGRAM__ = {{
  "name": "Pipeline: {name_a} -> {name_b}",
  "version": "1.0",
  "description": "Runs program A then feeds its output into program B.",
  "params": {json.dumps(params_all, ensure_ascii=False, indent=2)},
  "kind": "module"
}}

def _safe_str(x):
  if isinstance(x, (dict, list)):
    try:
      return json.dumps(x, ensure_ascii=False, indent=2)
    except Exception:
      return str(x)
  return str(x)

def run(params: dict) -> str:
  # A params
  a_params = {{}}
"""
    if isinstance(schema_a, list):
        for it in schema_a:
            if isinstance(it, dict) and isinstance(it.get("key"), str) and it.get("key"):
                k = str(it["key"])
                wrapper += f"  if '{k}' in params:\n    a_params['{k}'] = params['{k}']\n"

    wrapper += f"""
  out_a = jarvis_runtime.call_program_by_index({idx_a}, a_params)

  # B params
  b_params = {{}}
  b_params[{b_input_key!r}] = out_a
"""

    if isinstance(schema_b, list):
        for it in schema_b:
            if not (isinstance(it, dict) and isinstance(it.get("key"), str) and it.get("key")):
                continue
            k = str(it["key"])
            if k == b_input_key:
                continue
            wrapper += f"  if 'b_{k}' in params:\n    b_params['{k}'] = params['b_{k}']\n"

    wrapper += f"""
  out_b = jarvis_runtime.call_program_by_index({idx_b}, b_params)
  return out_b if isinstance(out_b, str) else _safe_str(out_b)
"""
    return wrapper


def pipeline_ab_flow() -> None:
    """
    A→B パイプライン合体（実行）
    - Aを実行
    - 出力をBのどれかの入力キーに流し込む（推測 or 選択）
    - Bを実行
    - 希望があれば「合体した新プログラム」として登録
    """
    progs = list_programs()
    if len(progs) < 2:
        print("パイプラインには2つ以上のプログラムが必要です。")
        return

    print("\n--- A（先に実行）を選択 ---")
    for i, p in enumerate(progs):
        print(f"{i}: {p['name']} v{p['version']}")
    sel_a = input("Aの番号: ").strip()
    if not (sel_a.isdigit() and 0 <= int(sel_a) < len(progs)):
        print("無効な番号です。")
        return
    idx_a = int(sel_a)

    print("\n--- B（後に実行）を選択 ---")
    for i, p in enumerate(progs):
        print(f"{i}: {p['name']} v{p['version']}")
    sel_b = input("Bの番号: ").strip()
    if not (sel_b.isdigit() and 0 <= int(sel_b) < len(progs)):
        print("無効な番号です。")
        return
    idx_b = int(sel_b)

    if idx_a == idx_b:
        print("A と B は別のプログラムを選んでください。")
        return

    schema_a, _kind_a = _get_schema_and_kind(idx_a)
    schema_b, _kind_b = _get_schema_and_kind(idx_b)

    if schema_a is not None:
        params_a = prompt_params_from_schema(schema_a)
    else:
        print("(A: スキーマ未定義: key=value 方式で入力)")
        params_a = prompt_params()

    try:
        out_a = run_program_by_index(idx_a, params_a)
    except Exception as e:
        print("[エラー] Aの実行に失敗:", e)
        return

    # Bに流し込むキー決定
    b_input_key = _infer_b_input_key(schema_b)
    if not b_input_key:
        keys: List[str] = []
        if isinstance(schema_b, list):
            for it in schema_b:
                if isinstance(it, dict) and isinstance(it.get("key"), str) and it.get("key"):
                    keys.append(str(it["key"]))
        print("\n[B入力キー選択] 自動推測できませんでした。Bのparamsキー候補:")
        print("  " + ", ".join(keys) if keys else "  (候補なし)")
        chosen = input("Aの出力を入れるBのキーを入力: ").strip()
        if chosen and chosen in keys:
            b_input_key = chosen
        else:
            print("無効。キャンセルします。")
            return

    # B params：b_input_key は out_a で自動注入（ユーザーに聞かない）
    prefill_b = {b_input_key: out_a}

    if schema_b is not None:
        params_b = prompt_params_from_schema(schema_b, prefill=prefill_b)
    else:
        print("(B: スキーマ未定義: key=value 方式で入力)")
        params_b = prompt_params()
        params_b.update(prefill_b)

    try:
        out_b = run_program_by_index(idx_b, params_b)
    except Exception as e:
        print("[エラー] Bの実行に失敗:", e)
        return

    print("\n== パイプライン結果 ==")
    print("---- A output ----")
    print(_safe_str(out_a))
    print("---- B output ----")
    print(_safe_str(out_b))

    ok = input("\nこのA→Bを“合体した新プログラム”として登録しますか？ (y/n): ").strip().lower()
    if ok == "y":
        wrapper_code = _build_pipeline_wrapper_code(idx_a, idx_b, b_input_key)
        res = gate(wrapper_code)
        print("\n--- 合体プログラムの品質ゲート ---")
        print(format_result(res))
        if not res.ok:
            ok2 = input("品質ゲートに通っていませんが登録しますか？ (y/n): ").strip().lower()
            if ok2 != "y":
                print("キャンセルしました。")
                return

        path = save_program(wrapper_code)
        meta = register_program(path)
        print(f"[登録完了] {meta['name']}  v{meta['version']}  -> {meta['file']}")


def main():
    while True:
        choice = menu()

        # 1) Generate + preflight auto-fix
        if choice == 1:
            spec = input("どんなプログラムを追加したい？: ").strip()
            if not spec:
                print("空の要求は受け付けません。")
                continue

            print("\n[生成中] プログラムを生成します…")
            try:
                code, gate_res, regens = generate_with_preflight(spec, max_regens=2)
            except Exception as e:
                print("[エラー] 生成に失敗:", e)
                continue

            print("\n--- 品質ゲート結果 ---")
            print(format_result(gate_res))
            if regens:
                print(f"(自動再生成: {regens} 回)")

            print("\n--- 生成されたプログラム（保存前の確認） ---\n")
            print(code)

            if gate_res.ok:
                ok = input("\nこのプログラムを登録しますか？ (y/n): ").strip().lower()
            else:
                ok = input("\n[注意] まだ品質ゲートに通っていません。それでも登録しますか？ (y/n): ").strip().lower()

            if ok != "y":
                print("キャンセルしました。")
                continue

            path = save_program(code)
            meta = register_program(path)
            print(f"[登録完了] {meta['name']}  v{meta['version']}  -> {meta['file']}")

        # 2) List
        elif choice == 2:
            progs = list_programs()
            if not progs:
                print("まだプログラムはありません。")
                continue
            print("\n--- 登録済みプログラム一覧 ---")
            for i, p in enumerate(progs):
                print(f"{i}: {p['name']} v{p['version']}  ({p['file']})")

        # 3) Run
        elif choice == 3:
            progs = list_programs()
            if not progs:
                print("まだプログラムはありません。")
                continue

            print("\n--- 実行するプログラムを選択 ---")
            for i, p in enumerate(progs):
                print(f"{i}: {p['name']} v{p['version']}")

            sel = input("番号: ").strip()
            if not (sel.isdigit() and 0 <= int(sel) < len(progs)):
                print("無効な番号です。")
                continue
            idx = int(sel)

            # スキーマを読む（壊れてても落ちない）
            schema, kind = _get_schema_and_kind(idx)

            if schema is not None:
                params = prompt_params_from_schema(schema)
            else:
                print("(スキーマ未定義: key=value 方式で入力)")
                params = prompt_params()

            try:
                out = run_program_by_index(idx, params)
                print("\n== 実行結果 ==")

                # project_generator は誤判定しない（kind or 返り値で判定）
                if kind == "project_generator" and looks_like_project_generator(out):
                    base = Path("./generated_projects") / f"project_{int(time.time())}"
                    base.mkdir(parents=True, exist_ok=True)
                    for relpath, src in out.items():
                        dst = base / relpath
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_text(src, encoding="utf-8")
                    print(f"プロジェクトを {base} 以下に生成しました。")
                else:
                    print(out)

            except Exception as e:
                print("[エラー] 実行に失敗:", e)

        # 4) Edit (自動で自己評価→必要なら再生成)
        elif choice == 4:
            progs = list_programs()
            if not progs:
                print("まだプログラムはありません。")
                continue

            for i, p in enumerate(progs):
                print(f"{i}: {p['name']} v{p['version']}")
            sel = input("編集する番号: ").strip()
            if not (sel.isdigit() and 0 <= int(sel) < len(progs)):
                print("無効な番号です。")
                continue
            idx = int(sel)

            src = read_program_source_by_index(idx)
            print("\n--- 現在のコード（先頭40行） ---\n")
            print("\n".join(src.splitlines()[:40]))

            req = input("\nどんな変更をしたい？: ").strip()
            if not req:
                print("キャンセルしました。")
                continue

            spec = (
                "Apply the requested changes to the existing module.\n"
                "Return ONLY the full updated Python module.\n\n"
                "=== Existing code ===\n"
                f"{src}\n\n"
                "=== Requested changes ===\n"
                f"{req}\n"
            )

            print("\n[生成中] 修正版を生成します…")
            try:
                new_code, gate_res, regens = generate_with_preflight(spec, max_regens=2)
            except Exception as e:
                print("[エラー] 生成に失敗:", e)
                continue

            print("\n--- 品質ゲート結果 ---")
            print(format_result(gate_res))
            if regens:
                print(f"(自動再生成: {regens} 回)")

            print("\n--- 修正後コード（保存前の確認） ---\n")
            print(new_code)

            if gate_res.ok:
                ok = input("\nこの内容で上書きしますか？ (y/n): ").strip().lower()
            else:
                ok = input("\n[注意] まだ品質ゲートに通っていません。それでも上書きしますか？ (y/n): ").strip().lower()

            if ok != "y":
                print("キャンセルしました。")
                continue

            meta = overwrite_program_by_index(idx, new_code)
            print(f"[上書き完了] {meta['name']} v{meta['version']}")

        # 5) Delete
        elif choice == 5:
            progs = list_programs()
            if not progs:
                print("まだプログラムはありません。")
                continue
            for i, p in enumerate(progs):
                print(f"{i}: {p['name']} v{p['version']}")
            sel = input("削除する番号: ").strip()
            if not (sel.isdigit() and 0 <= int(sel) < len(progs)):
                print("無効な番号です。")
                continue
            ok = input("本当に削除しますか？ (y/n): ").strip().lower()
            if ok != "y":
                print("キャンセルしました。")
                continue
            deleted = delete_program_by_index(int(sel))
            print(f"[削除完了] {deleted['name']} を削除しました。")

        # 6) A->B pipeline
        elif choice == 6:
            pipeline_ab_flow()

        else:
            print("終了します。")
            break


if __name__ == "__main__":
    main()
