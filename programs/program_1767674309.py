import jarvis_runtime

__PROGRAM__ = {
    "name": "Translation Program",
    "version": "1.0",
    "description": "A program to translate text into a specified language.",
    "params": [
        {
            "key": "text",
            "label": "Text to Translate",
            "type": "str",
            "required": True,
            "placeholder": "Enter the text you want to translate"
        },
        {
            "key": "target_lang",
            "label": "Target Language",
            "type": "str",
            "required": True,
            "choices": ["en", "es", "fr", "de", "ja", "zh"],
            "placeholder": "Enter the target language code (e.g., 'en' for English)"
        },
        {
            "key": "source_lang",
            "label": "Source Language (optional)",
            "type": "str",
            "required": False,
            "placeholder": "Enter the source language code (optional)"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    text = params['text']
    target_lang = params['target_lang']
    source_lang = params.get('source_lang', None)
    
    translated_text = jarvis_runtime.translate_text(text, target_lang, source_lang)
    return translated_text