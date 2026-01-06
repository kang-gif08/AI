import jarvis_runtime

__PROGRAM__ = {
    "name": "Translation Program",
    "version": "1.0",
    "description": "A program to translate text using DeepL API.",
    "params": [
        {
            "key": "text",
            "label": "Text to Translate",
            "type": "str",
            "required": True,
            "placeholder": "Enter text here"
        },
        {
            "key": "target_language",
            "label": "Target Language",
            "type": "select",
            "required": True,
            "choices": ["EN", "FR", "DE", "ES", "IT", "NL", "PL", "RU", "JA", "ZH"],
            "placeholder": "Select target language"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    text = params['text']
    target_language = params['target_language']
    api_key = jarvis_runtime.get_secret("DEEPL_API_KEY")
    
    translated_text = jarvis_runtime.translate_text(text, target_language, api_key)
    
    return translated_text