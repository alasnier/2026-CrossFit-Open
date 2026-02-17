"""
tests/test_integration.py
Tests d'intégration — nécessitent une vraie base PostgreSQL.
Configurer : export TEST_DATABASE_URL="postgresql://..."

Run : pytest tests/test_integration.py -v
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Skip tout le module si pas de DB de test configurée
TEST_DB = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DB, reason="TEST_DATABASE_URL non configurée")


@pytest.fixture(scope="module")
def engine():
    """Crée un engine sur la DB de test et les tables."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker

    eng = create_engine(TEST_DB, pool_pre_ping=True, future=True)
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def tables(engine):
    """Crée toutes les tables dans la DB de test."""
    # Import conditionnel pour éviter l'init Streamlit
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("DATABASE_URL", TEST_DB)
        from sqlalchemy.orm import declarative_base
        from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
        from sqlalchemy.orm import relationship

        Base = declarative_base()

        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String(255), nullable=False)
            email = Column(String(255), unique=True, nullable=False)
            password = Column(String(255), nullable=False)
            sex = Column(String(10), nullable=False)
            birth_year = Column(Integer, nullable=False)
            level = Column(String(10), nullable=False)
            category = Column(String(20), nullable=False)
            age = Column(Integer, nullable=False)
            scores = relationship("Score", back_populates="user", cascade="all, delete")

        class Score(Base):
            __tablename__ = "scores"
            id = Column(Integer, primary_key=True)
            user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
            wod = Column(String(10), nullable=False)
            score = Column(String(20), nullable=False)
            created_at = Column(TIMESTAMP, server_default=func.now())
            user = relationship("User", back_populates="scores")

        class Wod(Base):
            __tablename__ = "wods"
            wod = Column(String(10), primary_key=True)
            label = Column(String(100), nullable=False)
            type = Column(String(10), nullable=False)
            timecap_seconds = Column(Integer, nullable=True)

        Base.metadata.create_all(engine)
        yield Base, User, Score, Wod
        # Nettoyage
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="module")
def session_factory(engine, tables):
    from sqlalchemy.orm import sessionmaker
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return factory


@pytest.fixture(autouse=True)
def clean_tables(engine, tables):
    """Vide les tables avant chaque test."""
    Base, User, Score, Wod = tables
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    with Session() as s:
        s.query(Score).delete()
        s.query(User).delete()
        s.query(Wod).delete()
        s.commit()
    yield


# ─────────────────────────────────────────────
# Tests DB
# ─────────────────────────────────────────────

class TestUserCRUD:
    def test_create_user(self, session_factory, tables):
        _, User, _, _ = tables
        Session = session_factory
        with Session() as s:
            user = User(
                name="Test Athlete", email="test@crossfit.fr", password="hashed_pw",
                sex="Male", birth_year=1995, level="RX", category="Elite", age=31,
            )
            s.add(user)
            s.commit()
            found = s.query(User).filter_by(email="test@crossfit.fr").first()
            assert found is not None
            assert found.name == "Test Athlete"
            assert found.category == "Elite"

    def test_duplicate_email_raises(self, session_factory, tables):
        from sqlalchemy.exc import IntegrityError
        _, User, _, _ = tables
        Session = session_factory
        with Session() as s:
            s.add(User(name="A", email="dup@test.fr", password="pw",
                       sex="Female", birth_year=1990, level="Scaled", category="Masters", age=36))
            s.commit()
        with pytest.raises(IntegrityError):
            with Session() as s:
                s.add(User(name="B", email="dup@test.fr", password="pw",
                           sex="Male", birth_year=1985, level="RX", category="Masters", age=41))
                s.commit()

    def test_delete_user_cascades_scores(self, session_factory, tables):
        _, User, Score, Wod = tables
        Session = session_factory
        with Session() as s:
            # Créer wod
            s.add(Wod(wod="26.1", label="Open 26.1", type="reps", timecap_seconds=None))
            user = User(name="ToDelete", email="del@test.fr", password="pw",
                        sex="Male", birth_year=2000, level="RX", category="Elite", age=26)
            s.add(user)
            s.commit()
            s.add(Score(user_id=user.id, wod="26.1", score="150"))
            s.commit()
            assert s.query(Score).filter_by(user_id=user.id).count() == 1
            s.delete(user)
            s.commit()
            assert s.query(Score).filter_by(user_id=user.id).count() == 0


class TestWodSeed:
    def test_wod_seed_idempotent(self, engine, session_factory, tables):
        """ON CONFLICT DO NOTHING : seeder deux fois ne duplique pas."""
        from sqlalchemy import text
        _, _, _, Wod = tables
        Session = session_factory

        # Premier insert via ORM
        with Session() as s:
            s.add_all([
                Wod(wod="26.1", label="Open 26.1", type="reps", timecap_seconds=None),
                Wod(wod="26.2", label="Open 26.2", type="time", timecap_seconds=720),
                Wod(wod="26.3", label="Open 26.3", type="time", timecap_seconds=1200),
            ])
            s.commit()
        assert Session().query(Wod).count() == 3

        # Deuxième seed via SQL brut (comme bootstrap_after_create) → ne doit pas dupliquer
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO wods (wod, label, type, timecap_seconds)
                VALUES
                    ('26.1', 'Open 26.1', 'reps', NULL),
                    ('26.2', 'Open 26.2', 'time', 720),
                    ('26.3', 'Open 26.3', 'time', 1200)
                ON CONFLICT (wod) DO NOTHING
            """))

        # Le count doit toujours être 3, pas 6
        with Session() as s:
            assert s.query(Wod).count() == 3

    def test_wod_timecap_values(self, session_factory, tables):
        _, _, _, Wod = tables
        Session = session_factory
        with Session() as s:
            s.add_all([
                Wod(wod="26.1", label="Open 26.1", type="reps", timecap_seconds=None),
                Wod(wod="26.2", label="Open 26.2", type="time", timecap_seconds=720),
                Wod(wod="26.3", label="Open 26.3", type="time", timecap_seconds=1200),
            ])
            s.commit()
            w26_2 = s.query(Wod).filter_by(wod="26.2").first()
            w26_3 = s.query(Wod).filter_by(wod="26.3").first()
            assert w26_2.timecap_seconds == 720   # 12 * 60
            assert w26_3.timecap_seconds == 1200  # 20 * 60
            assert s.query(Wod).filter_by(wod="26.1").first().timecap_seconds is None


class TestScoreOperations:
    def _seed_base(self, session_factory, tables):
        _, User, Score, Wod = tables
        Session = session_factory
        with Session() as s:
            s.add_all([
                Wod(wod="26.1", label="Open 26.1", type="reps", timecap_seconds=None),
                Wod(wod="26.2", label="Open 26.2", type="time", timecap_seconds=720),
            ])
            user = User(name="Athlete A", email="a@cf.fr", password="pw",
                        sex="Male", birth_year=1995, level="RX", category="Elite", age=31)
            s.add(user)
            s.commit()
            return user.id

    def test_insert_reps_score(self, session_factory, tables):
        _, User, Score, Wod = tables
        Session = session_factory
        uid = self._seed_base(session_factory, tables)
        with Session() as s:
            s.add(Score(user_id=uid, wod="26.1", score="178"))
            s.commit()
            score = s.query(Score).filter_by(user_id=uid, wod="26.1").first()
            assert score.score == "178"

    def test_update_existing_score(self, session_factory, tables):
        _, User, Score, Wod = tables
        Session = session_factory
        uid = self._seed_base(session_factory, tables)
        with Session() as s:
            s.add(Score(user_id=uid, wod="26.1", score="150"))
            s.commit()
        with Session() as s:
            existing = s.query(Score).filter_by(user_id=uid, wod="26.1").first()
            existing.score = "200"
            s.commit()
        with Session() as s:
            updated = s.query(Score).filter_by(user_id=uid, wod="26.1").first()
            assert updated.score == "200"
            assert s.query(Score).filter_by(user_id=uid, wod="26.1").count() == 1

    def test_insert_time_score(self, session_factory, tables):
        _, User, Score, Wod = tables
        Session = session_factory
        uid = self._seed_base(session_factory, tables)
        with Session() as s:
            s.add(Score(user_id=uid, wod="26.2", score="09:45"))
            s.commit()
            score = s.query(Score).filter_by(user_id=uid, wod="26.2").first()
            assert score.score == "09:45"

    def test_insert_cap_score(self, session_factory, tables):
        _, User, Score, Wod = tables
        Session = session_factory
        uid = self._seed_base(session_factory, tables)
        with Session() as s:
            s.add(Score(user_id=uid, wod="26.2", score="CAP:05"))
            s.commit()
            score = s.query(Score).filter_by(user_id=uid, wod="26.2").first()
            assert score.score == "CAP:05"


class TestClassementQuery:
    def _seed_full(self, session_factory, tables):
        _, User, Score, Wod = tables
        Session = session_factory
        with Session() as s:
            s.add_all([
                Wod(wod="26.1", label="Open 26.1", type="reps", timecap_seconds=None),
                Wod(wod="26.2", label="Open 26.2", type="time", timecap_seconds=720),
            ])
            users = [
                User(name="Alice", email="alice@cf.fr", password="pw", sex="Female",
                     birth_year=1995, level="RX", category="Elite", age=31),
                User(name="Bob", email="bob@cf.fr", password="pw", sex="Male",
                     birth_year=1993, level="RX", category="Elite", age=33),
                User(name="Charlie", email="charlie@cf.fr", password="pw", sex="Male",
                     birth_year=1993, level="Scaled", category="Elite", age=33),
            ]
            s.add_all(users)
            s.commit()
            alice = s.query(User).filter_by(email="alice@cf.fr").first()
            bob = s.query(User).filter_by(email="bob@cf.fr").first()
            charlie = s.query(User).filter_by(email="charlie@cf.fr").first()
            s.add_all([
                Score(user_id=alice.id, wod="26.1", score="185"),
                Score(user_id=bob.id, wod="26.1", score="210"),
                Score(user_id=charlie.id, wod="26.1", score="95"),
                Score(user_id=alice.id, wod="26.2", score="10:30"),
                Score(user_id=bob.id, wod="26.2", score="09:15"),
            ])
            s.commit()

    def test_classement_reps_filters_sex_level(self, session_factory, tables):
        _, User, Score, Wod = tables
        Session = session_factory
        self._seed_full(session_factory, tables)
        with Session() as s:
            rows = (
                s.query(User.name, Score.score)
                .join(Score, User.id == Score.user_id)
                .filter(Score.wod == "26.1", User.sex == "Male", User.level == "RX")
                .all()
            )
        assert len(rows) == 1
        assert rows[0][0] == "Bob"

    def test_classement_reps_desc_order(self, session_factory, tables):
        _, User, Score, _ = tables
        Session = session_factory
        self._seed_full(session_factory, tables)
        with Session() as s:
            rows = (
                s.query(User.name, Score.score)
                .join(Score, User.id == Score.user_id)
                .filter(Score.wod == "26.1")
                .all()
            )
        sorted_rows = sorted(rows, key=lambda r: int(r[1]), reverse=True)
        assert sorted_rows[0][0] == "Bob"  # 210 reps

    def test_no_results_returns_empty(self, session_factory, tables):
        _, User, Score, Wod = tables
        Session = session_factory
        with Session() as s:
            s.add(Wod(wod="26.3", label="Open 26.3", type="time", timecap_seconds=1200))
            s.commit()
        with Session() as s:
            rows = (
                s.query(User.name, Score.score)
                .join(Score, User.id == Score.user_id)
                .filter(Score.wod == "26.3")
                .all()
            )
        assert rows == []
