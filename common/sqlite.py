from typing import Optional
from datetime import datetime


def safe_boolean(value: Optional[int]) -> bool:
    if value is None:
        return value
    return value == 1


def safe_datetime(value: Optional[str]) -> datetime:
    if value is None:
        return value
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
