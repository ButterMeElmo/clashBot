from .meta import *

if __name__ == '__main__':
	# Create an engine that stores data in the local directory's
	# sqlalchemy_example.db file.
	engine = create_engine('sqlite:///clashData.db')
	 
	# Create all tables in the engine. This is equivalent to "Create Table"
	# statements in raw SQL.
	Base.metadata.create_all(engine)
