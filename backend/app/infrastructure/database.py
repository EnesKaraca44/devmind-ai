from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import DATABASE_URL

# Kısıt (constraint) adlarını tahmin edilebilir yapar. Alembic migration'larında
# "bu kısıtı sil" diyebilmek için her kısıtın sabit bir adı olmalı.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Tüm tablo sınıflarının atası. `Base.metadata` = bilinen tüm tabloların listesi;
    Alembic migration üretirken buna bakar."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def get_engine(url: str | None = None) -> Engine:
    """Engine = veritabanına açılan bağlantı havuzu. Adres yoksa net bir hata verir."""
    database_url = url or DATABASE_URL
    if not database_url:
        raise RuntimeError("DATABASE_URL tanımlı değil.")
    # pool_pre_ping: havuzdan alınan bağlantı ölmüşse kullanmadan önce fark edip yeniler.
    return create_engine(database_url, pool_pre_ping=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    # Session = "iş birimi": birkaç değişikliği biriktirir, commit ile hepsini birden yazar.
    return sessionmaker(bind=engine, expire_on_commit=False)


@lru_cache(maxsize=1)
def _default_session_factory() -> sessionmaker[Session]:
    # Engine (bağlantı havuzu) PAHALIDIR: uygulama boyunca BİR kez oluşturulur, her istek paylaşır.
    return make_session_factory(get_engine())


def get_session() -> Iterator[Session]:
    """FastAPI bağımlılığı: her istek için bir oturum açar, istek bitince kapatır."""
    with _default_session_factory()() as session:
        yield session
