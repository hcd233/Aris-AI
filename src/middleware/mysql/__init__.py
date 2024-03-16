from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from src.config import MYSQL_DATABASE, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, MYSQL_USER
from src.logger import logger

from .models import BaseSchema

MYSQL_LINK = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"


@logger.catch
def init_mysql_session() -> sessionmaker[Session]:

    engine = create_engine(
        MYSQL_LINK,
        connect_args={
            "charset": "utf8mb4",
        },
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_use_lifo=True,
        pool_recycle=3600,
    )

    session = sessionmaker(bind=engine)

    BaseSchema.metadata.create_all(engine)
    logger.info("Init session successfully")

    return session


session = init_mysql_session()
