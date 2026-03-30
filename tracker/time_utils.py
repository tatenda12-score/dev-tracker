from datetime import datetime
from zoneinfo import ZoneInfo


ZIMBABWE_TZ = ZoneInfo("Africa/Harare")


def now_harare() -> datetime:
    return datetime.now(ZIMBABWE_TZ).replace(tzinfo=None)


def ensure_harare(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZIMBABWE_TZ)
    return dt.astimezone(ZIMBABWE_TZ)
