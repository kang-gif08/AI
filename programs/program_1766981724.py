import jarvis_runtime

__PROGRAM__ = {
    "name": "English to Japanese Translator",
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
    # Here we would typically call a translation API, but for this example, we'll mock the response.
    translated_text = f"Translated: {text_to_translate} to Japanese"
    return translated_text