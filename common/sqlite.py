from datetime import datetime
from typing import Optional


def safe_boolean(value: Optional[int]) -> Optional[bool]:
    if value is None:
        return value
    return value == 1


def safe_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return value
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
