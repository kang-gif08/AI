import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import requests


WORKSPACE_DIR = Path("workspace")
SECRETS_DIR = WORKSPACE_DIR / "secrets"
TMP_DIR = WORKSPACE_DIR / "tmp"


def _safe_path(base: Path, rel: str) -> Path:
    base = base.resolve()
    p = (base / rel).resolve()
    if not str(p).startswith(str(base)):
        raise ValueError("unsafe path")
    return p


def read_text(rel_path: str, default: Optional[str] = None) -> str:
    p = _safe_path(WORKSPACE_DIR, rel_path)
    if not p.exists():
        if default is None:
            raise FileNotFoundError(str(p))
        return default
    return p.read_text(encoding="utf-8")


def write_text(rel_path: str, text: str) -> None:
    p = _safe_path(WORKSPACE_DIR, rel_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def read_json(rel_path: str, default: Optional[Any] = None) -> Any:
    raw = read_text(rel_path, default=None)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if default is not None:
            return default
        raise


def write_json(rel_path: str, obj: Any) -> None:
    write_text(rel_path, json.dumps(obj, ensure_ascii=False, indent=2))


def get_secret(name: str, default: Optional[str] = None) -> str:
    """
    Read a secret from ./workspace/secrets/<name>.txt

    - Preferred: get_secret("WEATHER_API_KEY")  -> workspace/secrets/WEATHER_API_KEY.txt
    - Also accepts lower-case or slightly different forms and will try reasonable fallbacks.
    """
    raw = (name or "").strip()
    if not raw:
        raise ValueError("secret name must be a non-empty string")

    candidates = []
    # exact
    candidates.append(raw)
    # uppercase
    candidates.append(raw.upper())
    # common: "weather_api_key" -> "WEATHER_API_KEY"
    if raw.lower().endswith("api_key") and not raw.upper().endswith("_API_KEY"):
        candidates.append(
            __import__("re")
            .sub(r"api_key$", "_API_KEY", raw, flags=__import__("re").IGNORECASE)
            .upper()
        )

    filenames = []
    for c in candidates:
        if c.endswith(".txt"):
            filenames.append(c)
        else:
            filenames.append(f"{c}.txt")

    tried = []
    for fn in filenames:
        p = _safe_path(SECRETS_DIR, fn)
        tried.append(str(p))
        if p.exists():
            return p.read_text(encoding="utf-8").strip()

    if default is not None:
        return str(default)

    raise FileNotFoundError("Secret not found. Tried: " + ", ".join(tried))


def http_get_json(url: str, timeout: float = 10) -> Any:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def http_post_json(url: str, payload: Dict[str, Any], timeout: float = 10) -> Any:
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def http_post_form(
    url: str,
    form: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10,
):
    """POST application/x-www-form-urlencoded and return JSON or text.

    Many APIs (e.g., DeepL) expect form-encoded payloads rather than JSON.
    """
    resp = requests.post(url, data=form, headers=headers, timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        return resp.text


def translate_text(
    text: str,
    target_lang: str,
    source_lang: Optional[str] = None,
    *,
    preserve_formatting: bool = False,
) -> str:
    """Translate text using DeepL (DEEPL_API_KEY).

    Reads the API key from: ./workspace/secrets/DEEPL_API_KEY.txt
    - Free plan keys typically end with ':fx' and must use api-free.deepl.com
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    if not isinstance(target_lang, str) or not target_lang.strip():
        raise ValueError("target_lang must be a non-empty string")

    key = get_secret("DEEPL_API_KEY")
    host = "api-free.deepl.com" if key.strip().endswith(":fx") else "api.deepl.com"
    url = f"https://{host}/v2/translate"

    form: Dict[str, Any] = {
        "text": text,
        "target_lang": target_lang.strip().upper(),
        "preserve_formatting": 1 if preserve_formatting else 0,
    }
    if source_lang:
        form["source_lang"] = source_lang.strip().upper()

    data = http_post_form(
        url,
        form=form,
        headers={"Authorization": f"DeepL-Auth-Key {key}"},
        timeout=15,
    )

    if isinstance(data, dict):
        translations = data.get("translations")
        if (
            isinstance(translations, list)
            and translations
            and isinstance(translations[0], dict)
        ):
            out = translations[0].get("text")
            if isinstance(out, str):
                return out

        msg = data.get("message") or data.get("error")
        if msg:
            raise RuntimeError(f"DeepL error: {msg}")

    raise RuntimeError("Unexpected DeepL response")
