from datetime import datetime
from typing import Optional

import pytz
from pytz import BaseTzInfo

PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')


def today(tz: Optional[BaseTzInfo] = None) -> datetime:
    return datetime.now(tz=tz)
