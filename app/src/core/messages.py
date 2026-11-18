def content_text(content: object) -> str:
    """Return the plain text of a message's content.

    Some providers, such as Anthropic and Gemini, return a list of content blocks
    (text, tool calls, reasoning) instead of a string. Only the text blocks are kept.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content)


def http_status(error: BaseException) -> int | None:
    """Return the HTTP status code carried by a provider SDK error, if any."""
    for candidate in (error, getattr(error, "response", None)):
        for attribute in ("status_code", "code"):
            value = getattr(candidate, attribute, None)
            if isinstance(value, int) and 400 <= value < 600:
                return value
    return None


def describe_error(error: BaseException, limit: int = 300) -> str:
    """Return a one-line, length-limited description of ``error`` for the user."""
    message = str(error).strip().splitlines()[0] if str(error).strip() else ""
    if len(message) > limit:
        message = message[: limit - 3] + "..."
    return f"{type(error).__name__}: {message}" if message else type(error).__name__
