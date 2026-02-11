# infra/db.py
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

# Streamlit peut ne pas être dispo en contexte tests -> importer prudemment
try:
    import streamlit as st  # type: ignore
except Exception:  # pragma: no cover
    st = None  # type: ignore

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker | None = None
_BOOTSTRAPPED: bool = False


def _db_url() -> str:
    # 1) Streamlit secrets  2) fallback os.getenv
    url = None
    try:
        if st is not None:
            url = st.secrets.get("database", {}).get("url")  # type: ignore
    except Exception:
        pass
    return url or os.getenv("DATABASE_URL", "")


def get_engine() -> Engine:
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is None:
        url = _db_url()
        if not url:
            raise RuntimeError(
                "DATABASE_URL manquant (st.secrets['database']['url'] ou variable d'environnement)."
            )
        _ENGINE = create_engine(
            url,
            pool_size=5,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=1800,
            future=True,
        )
        _SESSION_FACTORY = sessionmaker(bind=_ENGINE, expire_on_commit=False, future=True)
    return _ENGINE


@contextmanager
def get_session(readonly: bool = False) -> Iterator[Session]:
    if _SESSION_FACTORY is None:
        get_engine()
    assert _SESSION_FACTORY is not None
    session = _SESSION_FACTORY()
    try:
        if readonly:
            session.execute(text("SET TRANSACTION READ ONLY"))
        yield session
        if not readonly:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def bootstrap_after_create() -> None:
    """
    Idempotent : insère les WODs 26.x + crée les index si absents.
    Appelée après Base.metadata.create_all(...).
    """
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    engine = get_engine()
    with engine.begin() as conn:
        # Seed 'wods' (ON CONFLICT pour idempotence)
        conn.execute(
            text("""
            INSERT INTO wods (wod, label, type, timecap_seconds)
            VALUES 
              ('26.1', 'Open 26.1', 'reps', NULL),
              ('26.2', 'Open 26.2', 'time', 12*60),
              ('26.3', 'Open 26.3', 'time', 20*60)
            ON CONFLICT (wod) DO NOTHING;
        """)
        )

        # Index idempotents
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_scores_user_wod ON scores(user_id, wod);")
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_sex_level ON users(sex, level);"))
    _BOOTSTRAPPED = True
