def uncapitalize(s: str) -> str:
    if not s:
        return s
    if len(s) == 1:
        return s.lower()
    return s[0].lower() + s[1:]
