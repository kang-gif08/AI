from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Callable

from ai_codegen import generate_program_best as generate_program
from registry import (
    save_program, register_program, list_programs, run_program_by_index,
    read_program_source_by_index, overwrite_program_by_index, delete_program_by_index
)

def prompt_params() -> Dict[str, Any]:
    """
    旧来の key=value 入力方式。
    値は JSON として解釈を試み、失敗したら文字列のまま扱う。
    """
    print("実行パラメータを key=value 形式で入力（空行で終了）。例: text=\"こんにちは\" count=3")
    params: Dict[str, Any] = {}
    while True:
        line = input("> ").strip()
        if not line:
            break
        if "=" not in line:
            print("  'key=value' で入力してください")
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        try:
            v_parsed = json.loads(v)
        except json.JSONDecodeError:
            v_parsed = v
        params[k] = v_parsed
    return params

def _cast_bool(val: str) -> bool:
    return val.lower() in ("1", "true", "t", "yes", "y", "on")

def _parse_list(val: str, elem_cast: Callable[[str], Any]) -> List[Any]:
    if not val.strip():
        return []
    return [elem_cast(x.strip()) for x in val.split(",") if x.strip()]

def prompt_params_from_schema(schema) -> Dict[str, Any]:
    """
    __PROGRAM__['params'] または __PARAMS_SCHEMA__ を前提とした対話入力。
    サポート型:
      - int, float, str, bool, select
      - list[int], list[float], list[str]
    """
    params: Dict[str, Any] = {}
    print("=== パラメータ入力（スキーマ） ===")
    for item in schema:
        key = item["key"]
        label = item.get("label", key)
        typ = item.get("type", "str")
        required = bool(item.get("required", False))
        default = item.get("default", "")
        choices = item.get("choices")
        placeholder = item.get("placeholder", "")

        hint_parts: List[str] = [f"[{typ}]"]
        if choices and typ == "select":
            hint_parts.append(f"選択肢: {', '.join(map(str, choices))}")
        if typ.startswith("list["):
            hint_parts.append("カンマ区切りで入力")
        if placeholder:
            hint_parts.append(f"例: {placeholder}")
        if default != "":
            hint_parts.append(f"default: {default}")
        hint = " ".join(hint_parts)

        while True:
            val = input(f"- {label} {hint}: ").strip()

            if val == "" and default != "":
                val = str(default)
            if val == "" and not required:
                break

            try:
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

def menu() -> int:
    print("\n=== Self-Extensible Programs (OpenAI / Jarvis) ===")
    print("1) 新しいプログラムを生成して登録する")
    print("2) 登録済みプログラムを一覧表示する")
    print("3) 登録済みプログラムを実行する")
    print("4) 登録済みプログラムを編集する（機能追加・変更）")
    print("5) 登録済みプログラムを削除する")
    print("6) 終了")
    while True:
        sel = input("> 番号: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= 6:
            return int(sel)
        print("  無効な入力です。")

def looks_like_project_generator(out: Any) -> bool:
    """
    project_generator の返り値かどうかを安全に判定する。
    - dict[str,str] である
    - キーがファイルパスっぽい（.py/.json/.txt）
    """
    if not isinstance(out, dict):
        return False
    if len(out) == 0:
        return False
    for k, v in out.items():
        if not isinstance(k, str) or not isinstance(v, str):
            return False
        if not k.endswith((".py", ".json", ".txt")):
            return False
    return True

def main():
    while True:
        choice = menu()
        if choice == 1:
            spec = input("どんなプログラムを追加したい？: ").strip()
            print("\n[生成中] OpenAI API でプログラムを生成します...")
            try:
                code = generate_program(spec)
            except Exception as e:
                print("[エラー] 生成に失敗:", e)
                continue
            print("\n--- 生成されたプログラム（保存前の確認） ---\n")
            print(code)
            ok = input("\nこのプログラムを登録しますか？ (y/n): ").strip().lower()
            if ok != "y":
                print("キャンセルしました。")
                continue
            path = save_program(code)
            meta = register_program(path)
            print(f"[登録完了] {meta['name']}  v{meta['version']}  -> {meta['file']}")

        elif choice == 2:
            progs = list_programs()
            if not progs:
                print("まだプログラムはありません。")
            else:
                print("\n== 登録済みプログラム ==")
                for i, p in enumerate(progs):
                    print(f"{i}: {p['name']} v{p['version']} - {p['description']}")

        elif choice == 3:
            progs = list_programs()
            if not progs:
                print("まだプログラムはありません。")
                continue
            for i, p in enumerate(progs):
                print(f"{i}: {p['name']} v{p['version']}")
            sel = input("実行する番号を選択: ").strip()
            if not (sel.isdigit() and 0 <= int(sel) < len(progs)):
                print("無効な番号です。")
                continue

            try:
                from registry import load_module_by_index  # type: ignore
                mod = load_module_by_index(int(sel))
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
                out = run_program_by_index(int(sel), params)
                print("\n== 実行結果 ==")

                # ★ここが安全化ポイント：project_generator の誤判定を防ぐ
                if looks_like_project_generator(out):
                    base = Path("./generated_projects") / f"project_{int(time.time())}"
                    base.mkdir(parents=True, exist_ok=True)
                    for relpath, src in out.items():
                        dst = base / relpath
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_text(src, encoding="utf-8")
                    print(f"プロジェクトを {base} 以下に生成しました。")
                    print("生成されたファイル一覧:")
                    for relpath in out.keys():
                        print(" -", (base / relpath))
                else:
                    print(out)

            except Exception as e:
                print("[エラー] 実行に失敗:", e)

        elif choice == 4:
            progs = list_programs()
            if not progs:
                print("まだプログラムはありません。")
                continue
            for i, p in enumerate(progs):
                print(f"{i}: {p['name']} v{p['version']}")
            sel = input("編集する番号を選択: ").strip()
            if not (sel.isdigit() and 0 <= int(sel) < len(progs)):
                print("無効な番号です。")
                continue

            src = read_program_source_by_index(int(sel))
            head = "\n".join(src.splitlines()[:40])
            print("\n--- 現在の先頭40行（参考） ---\n")
            print(head)
            print("\n編集方法を選んでください：")
            print("  1) LLMに“機能追加/変更”を依頼して上書き")
            print("  2) 自分で全文を貼り付けて置き換え（手動）")
            m = input("> 番号: ").strip()

            if m == "1":
                req = input("どのように変更しますか？（例：count引数を追加して…）: ").strip()
                spec = (
                    "以下の既存モジュールに対し、指定の変更を加えた完全版を出力してください。\n"
                    "【既存】\n```python\n" + src + "\n```\n"
                    "【変更要求】\n" + req + "\n"
                    "注意: 出力はコードのみ。__PROGRAM__ と run(params) を必ず維持/更新。"
                )
                try:
                    new_code = generate_program(spec)
                except Exception as e:
                    print("[エラー] 生成に失敗:", e)
                    continue
                print("\n--- 生成された“修正後”プログラム（保存前の確認） ---\n")
                print(new_code)
                ok = input("\nこの内容で上書きしますか？ (y/n): ").strip().lower()
                if ok != "y":
                    print("キャンセルしました。")
                    continue
                meta = overwrite_program_by_index(int(sel), new_code)
                print(f"[更新完了] {meta['name']}  v{meta['version']} に更新しました。")

            elif m == "2":
                print("新しいプログラムの“全文”を貼り付け、最後に空行→Ctrl+Z→Enter（PowerShell）で確定してください。")
                print("(ヒント: まずエディタで用意してからコピペすると安全)")
                buf = []
                while True:
                    try:
                        line = input()
                    except EOFError:
                        break
                    if line is None:
                        break
                    buf.append(line)
                new_code = "\n".join(buf).strip()
                if not new_code:
                    print("入力が空です。中止します。")
                    continue
                meta = overwrite_program_by_index(int(sel), new_code)
                print(f"[更新完了] {meta['name']}  v{meta['version']} に更新しました。")
            else:
                print("無効な番号です。")

        elif choice == 5:
            progs = list_programs()
            if not progs:
                print("まだプログラムはありません。")
                continue
            for i, p in enumerate(progs):
                print(f"{i}: {p['name']} v{p['version']}")
            sel = input("削除する番号を選択: ").strip()
            if not (sel.isdigit() and 0 <= int(sel) < len(progs)):
                print("無効な番号です。")
                continue
            ok = input("本当に削除しますか？ (y/n): ").strip().lower()
            if ok != "y":
                print("キャンセルしました。")
                continue
            deleted = delete_program_by_index(int(sel))
            print(f"[削除完了] {deleted['name']} を削除しました。")

        else:
            print("終了します。")
            break

if __name__ == "__main__":
    main()
