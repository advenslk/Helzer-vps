from __future__ import annotations

import os


def admin_user_ids() -> frozenset[int]:
    raw = os.getenv("ADMIN_USER_IDS", "")
    ids: set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if item.isdigit():
            ids.add(int(item))
    return frozenset(ids)


def is_admin(user_id: int) -> bool:
    return user_id in admin_user_ids()
