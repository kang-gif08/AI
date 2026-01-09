import jarvis_runtime

__PROGRAM__ = {
    "name": "TextStatisticsTool",
    "version": "1.0",
    "description": "A tool to analyze text and provide statistics including character count, line count, empty line count, word count, and top 10 frequent words.",
    "params": [
        {
            "key": "text",
            "label": "Input Text",
            "type": "str",
            "required": True,
            "placeholder": "Enter your text here..."
        }
    ],
    "kind": "module"
}

def run(params: dict):
    text = params['text']
    
    # Calculate statistics
    lines = text.splitlines()
    line_count = len(lines)
    empty_line_count = sum(1 for line in lines if not line.strip())
    word_count = sum(len(line.split()) for line in lines)
    character_count = len(text)
    
    # Count word frequencies
    from collections import Counter
    words = text.split()
    word_frequencies = Counter(words)
    top_10_words = word_frequencies.most_common(10)
    
    # Format the output
    result = (
        f"Character Count: {character_count}\n"
        f"Line Count: {line_count}\n"
        f"Empty Line Count: {empty_line_count}\n"
        f"Word Count: {word_count}\n"
        f"Top 10 Frequent Words: {', '.join(f'{word} ({count})' for word, count in top_10_words)}"
    )
    
    return result