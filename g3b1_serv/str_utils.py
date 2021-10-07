def uncapitalize(s: str) -> str:
    if not s:
        return s
    if len(s) == 1:
        return s.lower()
    return s[0].lower() + s[1:]


def code(text: str) -> str:
    return f'<code>{text}</code>'


def bold(text: str) -> str:
    return f'<b>{text}</b>'


def italic(text: str) -> str:
    return f'<i>{text}</i>'

