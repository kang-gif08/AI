from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional, Tuple

from ai_codegen import generate_program_best as generate_program
from registry import (
    save_program, register_program, list_programs, run_program_by_index,
    read_program_source_by_index, overwrite_program_by_index, delete_program_by_index,
    load_module_by_index
)
import quality_gate


def prompt_params() -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    print("パラメータを key=value で入力してください。空行で終了。")
    while True:
        line = input("> ").strip()
        if not line:
            break
        if "=" not in line:
            print("  形式: key=value")
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            continue
        try:
            params[k] = json.loads(v)
        except Exception:
            params[k] = v
    return params

def _cast_bool(s: str) -> bool:
    s = s.strip().lower()
    if s in ("1", "true", "t", "yes", "y", "on"):
        return True
    if s in ("0", "false", "f", "no", "n", "off"):
        return False
    raise ValueError("bool は true/false, yes/no, 1/0 で入力してください")

def _parse_list(s: str, caster: Callable[[str], Any]) -> List[Any]:
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        raw = json.loads(s)
        if not isinstance(raw, list):
            raise ValueError("list は JSON 配列で入力してください")
        return [caster(str(x)) for x in raw]
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return [caster(p) for p in parts]

def prompt_params_from_schema(schema: Any) -> Dict[str, Any]:
    if not isinstance(schema, list) or not all(isinstance(x, dict) for x in schema):
        print("[警告] params スキーマが壊れています。key=value 方式にフォールバックします。")
        return prompt_params()

    params: Dict[str, Any] = {}
    print("=== パラメータ入力（スキーマ） ===")
    for item in schema:
        key = item.get("key")
        if not isinstance(key, str) or not key.strip():
            continue

        label = item.get("label", key)
        typ = item.get("type", "str")
        required = bool(item.get("required", False))
        default = item.get("default", None)
        placeholder = item.get("placeholder", None)
        choices = item.get("choices", None)

        example = None
        if isinstance(placeholder, str) and placeholder.strip():
            example = placeholder.strip()
        elif default is not None:
            example = str(default)

        line = f"- {label} [{typ}]"
        if choices:
            if isinstance(choices, list):
                show = choices[:12]
                line += f" 選択肢: {show}"
                if len(choices) > 12:
                    line += " ...(+more)"
        if example:
            line += f" 例: {example}"
        if (default is not None) and (typ != "bool"):
            line += f" default: {default}"
        if required:
            line += " (required)"
        print(line)

        while True:
            raw = input(f"  {key}> ").strip()

            if raw == "":
                if default is not None:
                    params[key] = default
                    break
                if required:
                    print("  必須です。入力してください。")
                    continue
                params[key] = None
                break

            try:
                if typ == "str":
                    casted = raw
                elif typ == "int":
                    casted = int(raw)
                elif typ == "float":
                    casted = float(raw)
                elif typ == "bool":
                    casted = _cast_bool(raw)
                elif typ == "select":
                    if not isinstance(choices, list) or not choices:
                        raise ValueError("select に choices がありません")
                    if raw not in choices:
                        print(f"  無効です。{choices} から選んでください。")
                        continue
                    casted = raw
                elif typ == "list[int]":
                    casted = _parse_list(raw, int)
                elif typ == "list[float]":
                    casted = _parse_list(raw, float)
                elif typ == "list[str]":
                    casted = _parse_list(raw, str)
                else:
                    try:
                        casted = json.loads(raw)
                    except Exception:
                        casted = raw

                params[key] = casted
                break
            except Exception as e:
                print("  入力が無効:", e)

    return params


def looks_like_project_generator(out: Any) -> bool:
    if not isinstance(out, dict):
        return False
    if not out:
        return False
    for k, v in out.items():
        if not isinstance(k, str) or not isinstance(v, str):
            return False
        if not k or k.startswith("/") or ".." in k:
            return False
    return True

def _maybe_save_generated_project(files: Dict[str, str]) -> None:
    print("\n== project_generator 出力（ファイル一覧）==")
    for rel in files.keys():
        print(" -", rel)

    ok = input("この出力をファイルとして保存しますか？ (y/n): ").strip().lower()
    if ok != "y":
        print("保存しませんでした（ターミナル上の出力のみ）。")
        return

    base = Path("./generated_projects") / f"project_{int(time.time())}"
    base.mkdir(parents=True, exist_ok=True)
    for relpath, src in files.items():
        dst = base / relpath
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src, encoding="utf-8")
    print(f"[保存完了] {base} 以下に生成しました。")


def generate_with_autofix(user_spec: str, max_rounds: int = 4) -> Tuple[str, quality_gate.GateResult]:
    spec = user_spec
    last_gate: Optional[quality_gate.GateResult] = None

    for _ in range(max_rounds):
        code = generate_program(spec)
        gate_res = quality_gate.gate(code)
        last_gate = gate_res
        if gate_res.ok:
            return code, gate_res

        errs = "\n".join(gate_res.errors[:12])
        spec = (
            "Fix the Python module so it passes the Jarvis quality gate.\n"
            "Do NOT include markdown. Output code only.\n\n"
            f"Original user request:\n{user_spec}\n\n"
            f"Quality gate errors:\n{errs}\n\n"
            "Last failed module:\n```python\n" + code + "\n```"
        )

    return code, last_gate or quality_gate.GateResult(ok=False, errors=["Unknown"], warnings=[], tests=[])


def menu() -> int:
    print("\n=== Self-Extensible Jarvis ===")
    print("1) 新しいプログラムを生成して登録する（品質ゲート + 自動修正）")
    print("2) 登録済みプログラムを一覧表示する")
    print("3) 登録済みプログラムを実行する")
    print("4) 登録済みプログラムを編集する（機能追加・変更）")
    print("5) 登録済みプログラムを削除する")
    print("6) 自己評価→再生成（選択プログラムを自動改善）")
    print("7) ツール合成（プランを生成して連続実行）")
    print("8) 終了")
    while True:
        sel = input("> 番号: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= 8:
            return int(sel)

def _select_program_index() -> Optional[int]:
    progs = list_programs()
    if not progs:
        print("まだプログラムはありません。")
        return None
    for i, p in enumerate(progs):
        print(f"{i}: {p.get('name')} v{p.get('version')}")
    sel = input("> 番号: ").strip()
    if not (sel.isdigit() and 0 <= int(sel) < len(progs)):
        print("無効な番号です。")
        return None
    return int(sel)

def main():
    while True:
        choice = menu()

        if choice == 1:
            spec = input("どんなプログラムを追加したい？: ").strip()
            if not spec:
                continue

            print("\n[生成中] プログラムを生成し、品質チェックに通るまで自動修正します...")
            try:
                code, gate_res = generate_with_autofix(spec, max_rounds=4)
            except Exception as e:
                print("[エラー] 生成に失敗:", e)
                continue

            print("\n--- 生成されたプログラム（品質ゲート結果つき） ---\n")
            print(code)

            if gate_res.warnings:
                print("\n[警告]")
                for w in gate_res.warnings:
                    print(" -", w)

            if not gate_res.ok:
                print("\n[失敗] まだ品質ゲートに通っていません。エラー:")
                for er in gate_res.errors:
                    print(" -", er)
                ok = input("それでも登録しますか？ (y/n): ").strip().lower()
                if ok != "y":
                    print("キャンセルしました。")
                    continue
            else:
                print("\n[OK] 品質ゲートに合格しました。")

            ok = input("\nこのプログラムを登録しますか？ (y/n): ").strip().lower()
            if ok != "y":
                print("キャンセルしました。")
                continue
            path = save_program(code)
            meta = register_program(path, spec=spec)
            print(f"[登録完了] {meta['name']}  v{meta['version']}  -> {meta['file']}")

        elif choice == 2:
            progs = list_programs()
            if not progs:
                print("まだプログラムはありません。")
            else:
                print("\n== 登録済みプログラム ==")
                for i, p in enumerate(progs):
                    desc = p.get("description", "")
                    print(f"{i}: {p.get('name')} v{p.get('version')} - {desc}")

        elif choice == 3:
            idx = _select_program_index()
            if idx is None:
                continue

            try:
                mod = load_module_by_index(idx)
                schema = getattr(mod, "__PARAMS_SCHEMA__", None)
                if schema is None:
                    schema = getattr(mod, "__PROGRAM__", {}).get("params")
            except Exception:
                schema = None

            if schema:
                params = prompt_params_from_schema(schema)
            else:
                print("(スキーマ未定義: 従来の key=value 方式で入力)")
                params = prompt_params()

            try:
                out = run_program_by_index(idx, params)
                print("\n== 実行結果 ==")

                if looks_like_project_generator(out):
                    _maybe_save_generated_project(out)  # type: ignore[arg-type]
                else:
                    print(out)
            except Exception as e:
                print("[エラー] 実行に失敗:", e)

        elif choice == 4:
            idx = _select_program_index()
            if idx is None:
                continue

            src = read_program_source_by_index(idx)
            head = "\n".join(src.splitlines()[:40])
            print("\n--- 現在の先頭40行（参考） ---\n")
            print(head)

            print("\n編集方法を選んでください：")
            print("  1) LLMに“機能追加/変更”を依頼して上書き（品質ゲート + 自動修正）")
            print("  2) 自分で全文を貼り付けて置き換え（手動）")
            m = input("> 番号: ").strip()

            if m == "1":
                req = input("どのように変更しますか？: ").strip()
                spec = (
                    "Update the following module according to the change request.\n"
                    "Return the FULL updated module as code only.\n"
                    "Keep __PROGRAM__, run(params), and __TESTS__.\n\n"
                    "Existing module:\n```python\n" + src + "\n```\n\n"
                    "Change request:\n" + req
                )
                try:
                    new_code, gate_res = generate_with_autofix(spec, max_rounds=4)
                except Exception as e:
                    print("[エラー] 生成に失敗:", e)
                    continue

                print("\n--- 生成された編集後コード ---\n")
                print(new_code)
                if not gate_res.ok:
                    print("\n[警告] 編集後コードが品質ゲートに通っていません。")
                    for er in gate_res.errors:
                        print(" -", er)
                ok = input("\nこのコードで上書きしますか？ (y/n): ").strip().lower()
                if ok != "y":
                    print("キャンセルしました。")
                    continue

                meta = overwrite_program_by_index(idx, new_code, note=f"LLM edit: {req}")
                print(f"[更新完了] {meta['name']} v{meta['version']}")

            elif m == "2":
                print("\n--- ここから下に“全文”を貼り付けてください（空行3回で終了）---")
                lines: List[str] = []
                empty = 0
                while True:
                    line = input()
                    if line.strip() == "":
                        empty += 1
                    else:
                        empty = 0
                    lines.append(line)
                    if empty >= 3:
                        break
                new_code = "\n".join(lines).strip()
                gate_res = quality_gate.gate(new_code)
                if not gate_res.ok:
                    print("\n[警告] 品質ゲートに通っていません。エラー:")
                    for er in gate_res.errors:
                        print(" -", er)
                ok = input("\nそれでも上書きしますか？ (y/n): ").strip().lower()
                if ok != "y":
                    print("キャンセルしました。")
                    continue
                meta = overwrite_program_by_index(idx, new_code, note="manual overwrite")
                print(f"[更新完了] {meta['name']} v{meta['version']}")
            else:
                print("無効な選択です。")

        elif choice == 5:
            idx = _select_program_index()
            if idx is None:
                continue
            ok = input("本当に削除しますか？ (y/n): ").strip().lower()
            if ok != "y":
                print("キャンセルしました。")
                continue
            deleted = delete_program_by_index(idx)
            print(f"[削除完了] {deleted.get('name')} を削除しました。")

        elif choice == 6:
            idx = _select_program_index()
            if idx is None:
                continue

            progs = list_programs()
            spec = progs[idx].get("spec") if idx < len(progs) else None
            if not isinstance(spec, str) or not spec.strip():
                spec = input("改善の基準（仕様/目的）を入力してください: ").strip()

            src = read_program_source_by_index(idx)
            print("\n[評価] 現在のコードを品質ゲートで評価します...")
            gate_res = quality_gate.gate(src)
            if gate_res.ok:
                print("[OK] いまのコードは品質ゲートに合格しています。")
                ok = input("それでも改良（リファクタ/テスト追加/堅牢化）しますか？ (y/n): ").strip().lower()
                if ok != "y":
                    continue

            print("\n[改善中] 自動改善を試みます...")
            improve_spec = (
                "Improve the module to better satisfy the goal, strengthen edge cases, and improve tests.\n"
                "Return FULL module as code only.\n\n"
                f"Goal:\n{spec}\n\n"
                "Current module:\n```python\n" + src + "\n```"
            )
            try:
                new_code, new_gate = generate_with_autofix(improve_spec, max_rounds=4)
            except Exception as e:
                print("[エラー] 改善に失敗:", e)
                continue

            print("\n--- 改善後コード ---\n")
            print(new_code)
            if not new_gate.ok:
                print("\n[警告] 改善後も品質ゲートに通っていません。")
                for er in new_gate.errors:
                    print(" -", er)

            ok = input("\nこの改善を適用しますか？ (y/n): ").strip().lower()
            if ok != "y":
                continue
            meta = overwrite_program_by_index(idx, new_code, note="auto-improve")
            print(f"[更新完了] {meta.get('name')} v{meta.get('version')}")

        elif choice == 7:
            from planner import plan_and_execute
            goal = input("やりたいこと（目標）: ").strip()
            if not goal:
                continue
            try:
                out = plan_and_execute(goal)
                print("\n== プラン実行結果 ==")
                print(out)
            except Exception as e:
                print("[エラー] プラン実行に失敗:", e)

        else:
            print("終了します。")
            break

if __name__ == "__main__":
    main()
