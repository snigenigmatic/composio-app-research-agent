"""Load ./.env into os.environ (without overriding variables that are already set)."""
import os
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / ".env"


def load_env() -> None:
    if not ENV.exists():
        return
    for line in ENV.read_text(encoding="utf-8-sig").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            k, v = k.strip().removeprefix("export "), v.strip().strip('"').strip("'")
            if v and not os.environ.get(k):
                os.environ[k] = v


load_env()
