

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

database_url = "postgresql://postgres:1995@localhost:5432/postgres"

# disable sqlalchemy pool using NullPool as by default Postgres has its own pool
engine = create_engine(url=database_url, echo=True, poolclass=NullPool)

conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()
