import os
from collections.abc import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

Base = declarative_base()


def _make_engine() -> Engine:
    """Local/CI: DATABASE_URL with password. Azure: Managed Identity + Entra token."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url)

    from azure.identity import DefaultAzureCredential

    host = os.environ["DBHOST"]
    dbname = os.environ["DBNAME"]
    user = os.environ["DBUSER"]
    credential = DefaultAzureCredential()

    # Password filled in on each connect via Entra access token.
    url = (
        f"postgresql+psycopg2://{quote_plus(user)}:@{host}:5432/{dbname}"
        f"?sslmode=require"
    )
    engine = create_engine(url)

    @event.listens_for(engine, "do_connect")
    def _provide_token(dialect, conn_rec, cargs, cparams):
        token = credential.get_token(
            "https://ossrdbms-aad.database.windows.net/.default"
        ).token
        cparams["password"] = token

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
