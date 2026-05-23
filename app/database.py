from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 🔥 IMPORTANT : INJECTION FASTAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    url = make_url(settings.DATABASE_URL)

    if url.drivername.startswith("mysql"):
        temp_url = url._replace(database=None)
        temp_engine = create_engine(temp_url)

        with temp_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            conn.commit()

        temp_engine.dispose()

    from app.models.base import Base
    import app.models.user
    import app.models.room
    import app.models.message

    Base.metadata.create_all(bind=engine)