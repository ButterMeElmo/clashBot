from ClashBot.models.meta import Base

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    engine = create_engine("sqlite:///clashData.db")
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    Base.metadata.create_all(engine)
    # now all calls to Session() will create a thread-local session
    some_session = Session()
    try:
        yield some_session
        some_session.commit()
    except:
        some_session.rollback()
        raise
    finally:
        some_session.close()
