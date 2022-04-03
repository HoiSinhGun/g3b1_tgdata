import re


def uncapitalize(s: str) -> str:
    if not s:
        return s
    if len(s) == 1:
        return s.lower()
    return s[0].lower() + s[1:]


def camelize(string: str, uppercase_first_letter: bool = True) -> str:
    """
    Convert strings to CamelCase.
    Examples::
        >>> camelize("device_type")
        'DeviceType'
        >>> camelize("device_type", False)
        'deviceType'
    :func:`camelize` can be thought of as a inverse of :func:`underscore`,
    although there are some cases where that does not hold::
        >>> camelize(underscore("IOError"))
        'IoError'
    :param string: to be camelized
    :param uppercase_first_letter: if set to `True` :func:`camelize` converts
        strings to UpperCamelCase. If set to `False` :func:`camelize` produces
        lowerCamelCase. Defaults to `True`.
    """
    if uppercase_first_letter:
        return re.sub(r"(?:^|_)(.)", lambda m: m.group(1).upper(), string)
    else:
        return string[0].lower() + camelize(string)[1:]


def underscore(word: str) -> str:
    """
    Make an underscored, lowercase form from the expression in the string.
    Example::
        >>> underscore("DeviceType")
        'device_type'
    As a rule of thumb you can think of :func:`underscore` as the inverse of
    :func:`camelize`, though there are cases where that does not hold::
        >>> camelize(underscore("IOError"))
        'IoError'
    """
    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', word)
    word = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', word)
    word = word.replace("-", "_")
    return word.lower()


def code(text: str) -> str:
    return f'<code>{text}</code>'


def bold(text: str) -> str:
    return f'<b>{text}</b>'


# def spoiler(text: str) -> str:
#     return f'<b>{text}</b>'
#
#
def italic(text: str) -> str:
    return f'<i>{text}</i>'

