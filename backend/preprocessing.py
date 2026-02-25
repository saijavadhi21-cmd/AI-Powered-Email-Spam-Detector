import re
import html


def clean_text(text: str) -> str:
    if not text:
        return ''
    # unescape HTML entities
    text = html.unescape(text)
    # remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # remove URLs
    text = re.sub(r'http\S+|www\S+', ' ', text)
    # remove non-alphanumeric
    text = re.sub(r'[^A-Za-z0-9\s]', ' ', text)
    text = text.lower()
    # collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
