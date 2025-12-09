__PROGRAM__ = {
    "name": "TranslationModule",
    "version": "1.0",
    "description": "A simple translation module that translates text from one language to another.",
    "params": [
        {"key": "text", "label": "Text to Translate", "type": "str", "required": True, "placeholder": "Enter text here"},
        {"key": "source_lang", "label": "Source Language", "type": "select", "required": True, "choices": ["en", "ja", "fr", "es"], "placeholder": "Select source language"},
        {"key": "target_lang", "label": "Target Language", "type": "select", "required": True, "choices": ["en", "ja", "fr", "es"], "placeholder": "Select target language"},
        {"key": "capitalize", "label": "Capitalize Output", "type": "bool", "required": False, "default": False}
    ]
}

def run(params: dict) -> str:
    """
    Translates the given text from source language to target language.

    Args:
        params (dict): A dictionary containing 'text', 'source_lang', 'target_lang', and optional 'capitalize'.

    Returns:
        str: The translated text, optionally capitalized.
    """
    text = params.get("text", "")
    source_lang = params.get("source_lang", "en")
    target_lang = params.get("target_lang", "en")
    capitalize = params.get("capitalize", False)

    if not text or not source_lang or not target_lang:
        return "Invalid input: text, source_lang, and target_lang are required."

    # Simulated translation logic (for demonstration purposes)
    translated_text = f"Translated '{text}' from {source_lang} to {target_lang}"

    if capitalize:
        translated_text = translated_text.capitalize()

    return translated_text