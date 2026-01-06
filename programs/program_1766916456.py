import jarvis_runtime

__PROGRAM__ = {
    "name": "Translation Program",
    "version": "1.0",
    "description": "A program to translate text from one language to another.",
    "params": [
        {
            "key": "text",
            "label": "Text to Translate",
            "type": "str",
            "required": True,
            "placeholder": "Enter text here"
        },
        {
            "key": "source_language",
            "label": "Source Language",
            "type": "select",
            "required": True,
            "choices": ["en", "es", "fr", "de", "zh"],
            "placeholder": "Select source language"
        },
        {
            "key": "target_language",
            "label": "Target Language",
            "type": "select",
            "required": True,
            "choices": ["en", "es", "fr", "de", "zh"],
            "placeholder": "Select target language"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    text = params['text']
    source_language = params['source_language']
    target_language = params['target_language']
    
    # Simulate translation process
    translation_service_url = "https://api.example.com/translate"
    payload = {
        "text": text,
        "source": source_language,
        "target": target_language
    }
    
    response = jarvis_runtime.http_post_json(translation_service_url, payload)
    
    if response and 'translated_text' in response:
        return response['translated_text']
    else:
        return "Translation failed or returned no result."