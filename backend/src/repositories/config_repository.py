from sqlalchemy.orm import Session

from src.models.orm.config import Config


class ConfigRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str) -> str | None:
        row = self.db.get(Config, key)
        return row.value if row else None

    def set(self, key: str, value: str | None) -> None:
        row = self.db.get(Config, key)
        if row:
            row.value = value
        else:
            row = Config(key=key, value=value)
            self.db.add(row)
        self.db.commit()

    def bump_notice_version(self) -> int:
        cur = self.get("external_last_notice_version")
        try:
            n = int(cur) if cur is not None else 0
        except ValueError:
            n = 0
        n += 1
        self.set("external_last_notice_version", str(n))
        return n
