import bleach

ALLOWED_TAGS = [
    "b", "i", "strong", "em", "code", "pre", "p", "br",
    "ul", "ol", "li", "span", "blockquote"
]
ALLOWED_ATTRIBUTES = {
    "span": ["class"],
    "code": ["class"],
}


def sanitize_html(text: str) -> str:
    """Sanitizes user input string using bleach to strip malicious HTML/XSS vectors."""
    if not text:
        return text
    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
