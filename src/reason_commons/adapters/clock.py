from datetime import datetime, timezone


class UTCClock:
    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

