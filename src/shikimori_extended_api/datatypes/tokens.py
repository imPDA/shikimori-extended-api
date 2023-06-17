from datetime import timedelta, datetime, timezone

from pydantic import BaseModel


class ShikiToken(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: timedelta
    expires_at: datetime

    @property
    def is_expired(self):
        return datetime.now(tz=timezone.utc) > self.expires_at
