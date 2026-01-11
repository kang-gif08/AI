import jarvis_runtime

__PROGRAM__ = {
    "name": "文章の言い換えプログラム",
    "version": "1.3",
    "description": "日本語文章を、指定トーンに言い換えます（内容は変えない）。OpenAI APIを使用します。",
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
    
    # OpenAI APIを使って言い換えを行う
    prompt = f"次の文章を{tone}なトーンで言い換えてください: {text}"
    response = jarvis_runtime.http_post_json("https://api.openai.com/v1/engines/davinci-codex/completions", {
        "prompt": prompt,
        "max_tokens": 100
    })
    
    modified_text = response['choices'][0]['text'].strip()
    
    return modified_text