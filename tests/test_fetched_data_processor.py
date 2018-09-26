import pytest
from ClashBot.models import CLAN, MEMBER
from ClashBot import FetchedDataProcessor, DatabaseSetup
import os
from unittest import mock
from fake_data import test_process_player_achievement_files_processes_file_data 
import json

@pytest.fixture
def fetched_data_processor():
    """
    This is a fixture for use in all tests in the module.
    """
    return FetchedDataProcessor()

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
        db_results = test_db_session.query(CLAN).filter_by(clan_tag = clan_tag).all()
        assert len(db_results) == 1
        name_in_db = db_results[0].clan_name
        assert name_in_db == required_clan_name

@pytest.mark.parametrize('member_list', [[
        ('AWIOFJ','aowen', 'elder', 1523, 12),
        ('tag here','name here', 'co_leader', 235, 13),
        ('tag here', 'new name here', 'leader', 5007, 1)
        ]])
@pytest.mark.skip(reason="implementing scanned data first")
def test_add_members_to_db_defaults(test_db_session, fetched_data_processor, member_list):
    expected_results = {}
    for member in member_list:
        tag, name, role, trophies, th_level = member
        expected_results[tag] = member
        fetched_data_processor.addMemberToDB(test_db_session, tag, name, role, trophies, th_level)

    for tag in expected_results:
        tag, name, role, trophies, th_level = member
        db_results = test_db_session.query(MEMBER).filter_by(member_tag = tag).all()
        assert len(db_results) == 1
        member_results = db_results[0]
        assert member_results.member_tag == tag
        assert member_results.member_name == name
        assert member_results.role == role
        assert member_results.town_hall_level == trophies
        assert member_results.in_clan_currently == 1
        assert member_results.in_war_currently == 0
        assert member_results.last_seen_in_war == 0
        
@pytest.mark.parametrize('member_list', [[
        ('AWIOFJ','aowen', 'elder', 1523, 12, 1, 1, 1),
        ('tag here','name here', 'co_leader', 235, 13, 4523645, 1, 0),
        ('tag here', 'new name here', 'leader', 5007, 1, 4376583, 0, 1)
        ]])
@pytest.mark.skip(reason="implementing scanned data first")
def test_add_members_to_db(test_db_session, fetched_data_processor, member_list):
    expected_results = {}
    for member in member_list:
        tag, name, role, trophies, th_level, last_seen_in_war, in_clan, in_war = member
        expected_results[tag] = member
        fetched_data_processor.addMemberToDB(test_db_session, tag, name, role, trophies, th_level)

    for tag in expected_results:
        tag, name, role, trophies, th_level, last_seen_in_war, in_clan, in_war = member
        db_results = test_db_session.query(MEMBER).filter_by(member_tag = tag).all()
        assert len(db_results) == 1
        member_results = db_results[0]
        assert member_results.member_tag == tag
        assert member_results.member_name == name
        assert member_results.role == role
        assert member_results.town_hall_level == trophies
        assert member_results.in_clan_currently == in_clan
        assert member_results.in_war_currently == in_war
        assert member_results.last_seen_in_war == last_seen_in_war

def test_save_data_executes(test_db_session, fetched_data_processor):
    with mock.patch('ClashBot.FetchedDataProcessor.process_player_achievement_files', autospec=True) as process_player_achievement_files, \
            mock.patch('ClashBot.FetchedDataProcessor.process_clan_war_log_overview_files', autospec=True) as process_clan_war_files_overview, \
            mock.patch('ClashBot.FetchedDataProcessor.process_clan_war_details_files', autospec=True) as process_clan_war_files_details:
        fetched_data_processor.save_data(test_db_session, 657, "some_dir")
        process_player_achievement_files.assert_called_once_with(fetched_data_processor, test_db_session, 657, "some_dir")
        process_clan_war_files_details.assert_called_once_with(fetched_data_processor, test_db_session, 657, "some_dir")
        process_clan_war_files_overview.assert_called_once_with(fetched_data_processor, test_db_session, 657, "some_dir")

def test_process_player_achievement_files_throws(test_db_session, fetched_data_processor):
    with mock.patch('ClashBot.FetchedDataProcessor.process_clan_player_achievements', autospec=True) as process_clan_player_achievements:
        with pytest.raises(FileNotFoundError):
            fetched_data_processor.process_player_achievement_files(test_db_session, 1234, "rand_dir")


def test_process_player_achievement_files_processes_file(test_db_session, fetched_data_processor):
    fake_data_from_file = test_process_player_achievement_files_processes_file_data
    with mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(fake_data_from_file))) as mock_file, \
        mock.patch('ClashBot.FetchedDataProcessor.process_clan_player_achievements', autospec=True) as process_clan_player_achievements:
            # this time here is used to check for files (1 per day since that time in epoch). 
            # Usually if a file does not exist it is skipped, but since we are mocking the file reads,
            # open() is ALWAYS successful so this has the potential to be slow if we use the default 0 
            fetched_data_processor.process_player_achievement_files(test_db_session, 1537945719, "rand_dir")
            expected_calls = []
            for clan_player_achievements_entry in fake_data_from_file:
                expected_calls.append(mock.call(fetched_data_processor, test_db_session, clan_player_achievements_entry))
            process_clan_player_achievements.assert_has_calls(expected_calls)

