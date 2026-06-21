import re

OPERATORS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
}

_PATTERN = re.compile(r"^(%[\w]+%)\s*(>=|<=|==|!=|>|<)\s*(-?\d+(\.\d+)?)$")

def parse_condition(condition: str):
    match = _PATTERN.match(condition.strip())
    if not match:
        return None

    placeholder, operator, value, _ = match.groups()
    return placeholder, operator, float(value)

def evaluate_condition(condition: str, resolved_value: str) -> bool:
    parsed = parse_condition(condition)
    if not parsed:
        return False

    _, operator, expected = parsed

    try:
        actual = float(resolved_value)
    except (TypeError, ValueError):
        return False

    return OPERATORS[operator](actual, expected)
