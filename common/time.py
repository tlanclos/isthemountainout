from datetime import datetime, timezone
from typing import Optional

import pytz

PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')


def today(tz: Optional[timezone] = None) -> datetime:
    return datetime.now(tz=tz)
