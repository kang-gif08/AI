import jarvis_runtime

__PROGRAM__ = {
    "name": "TextDiff",
    "version": "1.0",
    "description": "行単位で2つのテキストを比較し、簡易diffを表示します。",
    "params": [
        {"key": "text1", "label": "テキスト1", "type": "str", "required": True, "placeholder": "最初のテキストを入力"},
        {"key": "text2", "label": "テキスト2", "type": "str", "required": True, "placeholder": "比較するテキストを入力"}
    ],
    "kind": "module"
}

def run(params: dict):
    text1 = params['text1'].splitlines()
    text2 = params['text2'].splitlines()
    
    diff = []
    max_lines = max(len(text1), len(text2))
    
    for i in range(max_lines):
        line1 = text1[i] if i < len(text1) else ""
        line2 = text2[i] if i < len(text2) else ""
        
        if line1 != line2:
            diff.append(f"Line {i + 1}:")
            if line1:
                diff.append(f"  - {line1}")
            if line2:
                diff.append(f"  + {line2}")
    
    return "\n".join(diff) if diff else "テキストに差分はありません。"