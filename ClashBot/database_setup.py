from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ClashBot.models.meta import Base

class DatabaseSetup:

    database_sessions = {}

    @staticmethod
    def get_session(engine_string = "sqlite:///clashData.db"):
        if engine_string in DatabaseSetup.database_sessions:
            return DatabaseSetup.database_sessions[engine_string]
        else:
            engine = create_engine(engine_string)
            Session = sessionmaker(bind=engine)

            # 1 - Base comes from the models module

            # 2 - generate database schema
            Base.metadata.create_all(engine)

            # 3 - create a new session
            session = Session()

            DatabaseSetup.database_sessions[engine_string] = session

            return session

if __name__ == '__main__':
        db_session = DatabaseSetup.get_session()
