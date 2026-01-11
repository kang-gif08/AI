import jarvis_runtime

__PROGRAM__ = {
    "name": "Text Summarizer",
    "version": "1.1",
    "description": "A program to summarize a given text by extracting key points.",
    "params": [
        {
            "key": "text",
            "label": "Text to Summarize",
            "type": "str",
            "required": True,
            "placeholder": "Enter the text you want to summarize"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    text = params['text']
    # Implementing a simple keyword extraction for summarization
    sentences = text.split('. ')
    important_sentences = sorted(sentences, key=lambda s: len(s), reverse=True)[:3]
    summary = ' '.join(important_sentences)
    return summary.strip() + '...'  # Return the summary with ellipsis to indicate continuation