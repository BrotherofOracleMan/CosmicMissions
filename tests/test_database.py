import pytest

from database import get_db


@pytest.mark.integration
def test_get_db_yields_session_and_closes():
    db_generator = get_db()
    session = next(db_generator)
    try:
        assert session is not None
        assert session.bind is not None
    finally:
        db_generator.close()
