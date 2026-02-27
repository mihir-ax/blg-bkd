import re


def auto_description(content: str, max_chars: int = 155) -> str:
    """Strip markdown symbols and return first `max_chars` chars as description."""
    clean = re.sub(r'#+\s', '', content)       # Remove heading markers
    clean = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', clean)  # Remove bold/italic
    clean = re.sub(r'!\[.*?\]\(.*?\)', '', clean)            # Remove images
    clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean) # Remove links
    clean = re.sub(r'`{1,3}.*?`{1,3}', '', clean, flags=re.DOTALL)  # Remove code
    clean = re.sub(r'\n+', ' ', clean).strip()
    return clean[:max_chars].rsplit(' ', 1)[0] + '…' if len(clean) > max_chars else clean


def auto_reading_time(content: str) -> int:
    """Estimate reading time in minutes (avg 200 words/min)."""
    word_count = len(content.split())
    minutes = max(1, round(word_count / 200))
    return minutes
