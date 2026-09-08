"""Load the clearly labelled prototype seed data. Safe to run more than once.

Usage (from apps/backend, with DATABASE_URL set):
    python scripts/seed.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.db.seed_data import seed_prototype_data  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        print(seed_prototype_data(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
