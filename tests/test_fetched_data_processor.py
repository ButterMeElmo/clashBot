import pytest
from ClashBot.models import CLAN
from ClashBot import FetchedDataProcessor, DatabaseSetup
import os

@pytest.fixture
def fetched_data_processor():
    """
    This is a fixture for use in all tests in the module.
    """
    return FetchedDataProcessor()

def test_create_database_if_not_exists():
    pass

@pytest.fixture
def test_db_session(tmpdir):
    """
    This is the db to be used for tests.
    """
    db_path = os.path.join(tmpdir.strpath, "test.db")
    return DatabaseSetup.get_session(engine_string = "sqlite:////" + db_path)

@pytest.mark.parametrize('clan_tag, clan_name', [
    ('AWIOFJ','aowen'),
    ('tag here','name here')
    ])
def test_add_clan_to_db_unique(test_db_session, fetched_data_processor, clan_tag, clan_name):
    fetched_data_processor.addClanToDB(test_db_session, clan_tag, clan_name)
    db_results = test_db_session.query(CLAN).all()
    number_of_clans = len(db_results)
    assert number_of_clans == 1

@pytest.mark.parametrize('clan_list', [[
    ('AWIOFJ','aowen'),
    ('tag here','name here')
    ]])
def test_add_clans_to_db_unique(test_db_session, fetched_data_processor, clan_list):
    for clan in clan_list:
        clan_tag, clan_name = clan
        fetched_data_processor.addClanToDB(test_db_session, clan_tag, clan_name)
    db_results = test_db_session.query(CLAN).all()
    number_of_clans = len(db_results)
    assert number_of_clans == len(clan_list)

@pytest.mark.parametrize('clan_list', [[
    ('AWIOFJ','aowen'),
    ('tag here','name here'),
    ('tag here', 'new name here')
    ]])
def test_add_clans_to_db_duplicates(test_db_session, fetched_data_processor, clan_list):
    result_dict = {}
    for clan in clan_list:
        clan_tag, clan_name = clan
        result_dict[clan_tag] = clan_name
        fetched_data_processor.addClanToDB(test_db_session, clan_tag, clan_name)

    # get the results from the db
    db_results = test_db_session.query(CLAN).all()
    number_of_clans = len(db_results)

    # validate we got what we want   
    assert number_of_clans == len(result_dict)

    for clan_tag in result_dict:
        required_clan_name = result_dict[clan_tag]
        db_results = test_db_session.query(CLAN).filter(clan_tag = clan_tag)
        assert len(db_results) == 1
        name_in_db = db_results[0].clan_tag
        assert name_in_db == required_clan_name
