import jarvis_runtime

__PROGRAM__ = {
    "name": "文章の言い換えプログラム",
    "version": "1.0",
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
    
    # 言い換え処理のためのリクエストを作成
    response = jarvis_runtime.translate_text(text, target_lang='ja')
    
    # トーンに応じた言い換えを行う
    if tone == "フォーマル":
        modified_text = f"フォーマルな表現: {response}"
    elif tone == "カジュアル":
        modified_text = f"カジュアルな表現: {response}"
    elif tone == "友好的":
        modified_text = f"友好的な表現: {response}"
    elif tone == "ビジネス":
        modified_text = f"ビジネスな表現: {response}"
    else:
        modified_text = response

    return modified_text