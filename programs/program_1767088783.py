import jarvis_runtime

__PROGRAM__ = {
    "name": "EnglishToJapaneseTranslator",
    "version": "1.0",
    "description": "Translates English text to Japanese.",
    "params": [
        {
            "key": "text",
            "label": "Text to Translate",
            "type": "str",
            "required": True,
            "placeholder": "Enter English text here"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    text_to_translate = params['text']
    translation_service_url = "https://api.example.com/translate"  # Replace with actual translation API URL
    response = jarvis_runtime.http_post_json(translation_service_url, {"text": text_to_translate, "target_lang": "ja"})
    
    if response.get("success"):
        return response.get("translated_text", "Translation failed.")
    else:
        return "Error in translation service."