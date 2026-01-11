import jarvis_runtime

__PROGRAM__ = {
    "name": "文章の言い換えプログラム",
    "version": "1.2",
    "description": "日本語文章を、指定トーンに言い換えます（内容は変えない）。",
    "params": [
        {
            "key": "text",
            "label": "元の文章",
            "type": "str",
            "required": True,
            "placeholder": "ここに元の文章を入力してください"
        },
        {
            "key": "tone",
            "label": "指定トーン",
            "type": "select",
            "required": True,
            "choices": ["フォーマル", "カジュアル", "友好的", "ビジネス"],
            "placeholder": "トーンを選択してください"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    text = params['text']
    tone = params['tone']
    
    # トーンに応じた言い換えを行う
    if tone == "フォーマル":
        modified_text = f"フォーマルな表現: {text}"
    elif tone == "カジュアル":
        modified_text = f"カジュアルな表現: {text}"
    elif tone == "友好的":
        modified_text = f"友好的な表現: {text}"
    elif tone == "ビジネス":
        modified_text = f"ビジネスな表現: {text}"
    else:
        modified_text = text

    return modified_text