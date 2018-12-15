import json
import os
import pytest

from unittest import mock

from ClashBot.models import CLAN, MEMBER, SCANNEDDATATIME, SCANNEDDATA, WAR, ACCOUNTNAME
from ClashBot import FetchedDataProcessor, DatabaseSetup

from fake_data import test_fetched_data_processor_fake_data

@pytest.fixture
def test_db_session(tmpdir):
    """
    This is the db to be used for tests.
    """
    db_path = os.path.join(tmpdir.strpath, "test.db")
    return DatabaseSetup.get_session(engine_string="sqlite:////" + db_path)


@pytest.fixture
def fetched_data_processor(test_db_session):
    """
    This is a fixture for use in all tests in the module.
    """
    return FetchedDataProcessor(test_db_session)


@pytest.mark.parametrize('clan_tag, clan_name', [
    ('AWIOFJ', 'aowen'),
    ('tag here', 'name here')
    ])
def test_add_clan_to_db_unique(test_db_session, fetched_data_processor, clan_tag, clan_name):
    fetched_data_processor.add_clan_to_db(clan_tag, clan_name)
    db_results = test_db_session.query(CLAN).all()
    number_of_clans = len(db_results)
    assert number_of_clans == 1


@pytest.mark.parametrize('clan_list', [[
    ('AWIOFJ', 'aowen'),
    ('tag here', 'name here')
    ]])
def test_add_clans_to_db_unique(test_db_session, fetched_data_processor, clan_list):
    for clan in clan_list:
        clan_tag, clan_name = clan
        fetched_data_processor.add_clan_to_db(clan_tag, clan_name)
    db_results = test_db_session.query(CLAN).all()
    number_of_clans = len(db_results)
    assert number_of_clans == len(clan_list)


@pytest.mark.parametrize('clan_list', [[
    ('AWIOFJ', 'aowen'),
    ('tag here', 'name here'),
    ('tag here', 'new name here')
    ]])
def test_add_clans_to_db_duplicates(test_db_session, fetched_data_processor, clan_list):
    result_dict = {}
    for clan in clan_list:
        clan_tag, clan_name = clan
        result_dict[clan_tag] = clan_name
        fetched_data_processor.add_clan_to_db(clan_tag, clan_name)

    # get the results from the db
    db_results = test_db_session.query(CLAN).all()
    number_of_clans = len(db_results)

    # validate we got what we want   
    assert number_of_clans == len(result_dict)

    for clan_tag in result_dict:
        required_clan_name = result_dict[clan_tag]
        db_results = test_db_session.query(CLAN).filter_by(clan_tag=clan_tag).all()
        assert len(db_results) == 1
        name_in_db = db_results[0].clan_name
        assert name_in_db == required_clan_name


@pytest.mark.parametrize('member_list', [[
        ('AWIOFJ', 'aowen', 'elder', 1523, 12),
        ('tag here', 'name here', 'co_leader', 235, 13),
        ('tag here', 'new name here', 'leader', 5007, 9)
        ]])
def test_add_members_to_db_defaults(test_db_session, fetched_data_processor, member_list):
    expected_results = {}
    for member in member_list:
        tag, name, role, trophies, th_level = member
        expected_results[tag] = member
        member_data = {
            'member_tag': tag,
            'member_name': name,
            'role': role,
            'trophies': trophies,
            'town_hall_level': th_level,
            'in_clan_currently': 0,
            'in_war_currently': 0,
            'last_updated_time': 2,
        }
        data_time = 3
        fetched_data_processor.add_or_update_member_in_db(data_time, **member_data)

    for _ in expected_results:
        tag, name, role, trophies, th_level = member
        db_results = test_db_session.query(MEMBER).filter_by(member_tag=tag).all()
        assert len(db_results) == 1
        member_results = db_results[0]
        assert member_results.member_tag == tag
        assert member_results.member_name == name
        assert member_results.role == role
        assert member_results.trophies == trophies
        assert member_results.town_hall_level == th_level
        assert member_results.in_clan_currently == 0
        assert member_results.in_war_currently == 0
        assert member_results.last_updated_time == 2


@pytest.mark.parametrize('member_list', [[
    ('AWIOFJ', 'aowen'),
    ('tag here', 'name here'),
    ('tag here', 'new name here')
]])
def test_add_account_name_to_db(test_db_session, fetched_data_processor, member_list):
    expected_results = {}
    for member_data in member_list:
        tag, name = member_data
        if tag in expected_results:
            expected_results[tag].append(member_data)
        else:
            expected_results[tag] = [member_data]
        fetched_data_processor.add_account_name_to_db(tag, name)

    for tag in expected_results:
        computed_results = test_db_session.query(ACCOUNTNAME).filter_by(member_tag=tag).all()
        assert computed_results == expected_results[tag]


@pytest.mark.parametrize('member_list', [[
        ('AWIOFJ', 'aowen', 'elder', 1523, 12, 1, 1, 1),
        ('tag here', 'name here', 'co_leader', 235, 13, 4523645, 1, 0),
        ('tag here', 'new name here', 'leader', 5007, 1, 4376583, 0, 1)
        ]])
def test_add_members_to_db(test_db_session, fetched_data_processor, member_list):
    expected_results = {}
    for member in member_list:
        tag, name, role, trophies, th_level, last_seen_in_war, in_clan, in_war = member
        expected_results[tag] = member
        member_data = {
            'member_tag': tag,
            'member_name': name,
            'role': role,
            'trophies': trophies,
            'town_hall_level': th_level,
            'in_clan_currently': 0,
            'in_war_currently': 0,
            'last_updated_time': 2,
        }
        data_time = 3
        fetched_data_processor.add_or_update_member_in_db(data_time, **member_data)

    for _ in expected_results:
        tag, name, role, trophies, th_level, last_seen_in_war, in_clan, in_war = member
        db_results = test_db_session.query(MEMBER).filter_by(member_tag=tag).all()
        assert len(db_results) == 1
        member_results = db_results[0]
        assert member_results.member_tag == tag
        assert member_results.member_name == name
        assert member_results.role == role
        assert member_results.trophies == trophies
        assert member_results.town_hall_level == th_level
        assert member_results.in_clan_currently == 0
        assert member_results.in_war_currently == 0
        assert member_results.last_updated_time == 2

@pytest.mark.parametrize('war_list', [
    [
    # (friendly_tag, enemy_tag, result, friendly_stars, enemy_stars, friendly_percentage, enemy_percentage, friendly_attacks_used, enemy_attacks_used, war_size, prep_day_start, war_day_start, war_day_end),
        ('#12341235', '#34534634', 'in progress', 15, 16, 60.453, 50.3, 5, 7, 15, 1542087769, 1542087770, 1542087777),
        ('#tag1', '#tag2', 'loss', 0, 30, 0.0, 100, 0, 10, 20, 234, 300, 400),
    ],
    [
        ('#12341235', '#34534634', 'in progress', 15, 16, 60.453, 50.3, 5, 7, 15, 1542087769, 1542087770, 1542087777),
        ('#tag1', '#tag2', 'loss', 0, 30, 0.0, 100, 0, 10, 20, 234, 300, 400),
        ('#12341235', '#34534634', 'win', 18, 17, 75.432, 63.643, 10, 15, 15, 1542087769, 1542087770, 1542087777),
    ],
])
def test_add_wars_to_db(test_db_session, fetched_data_processor, war_list):
    expected_results = {}
    for war_entry in war_list:
        friendly_tag, enemy_tag, result, friendly_stars, enemy_stars, friendly_percentage, enemy_percentage, friendly_attacks_used, enemy_attacks_used, war_size, prep_day_start, war_day_start, war_day_end = war_entry

        war_data = {
            'friendly_tag': friendly_tag,
            'enemy_tag': enemy_tag,
            'result': result,
            'friendly_stars': friendly_stars,
            'enemy_stars': enemy_stars,
            'friendly_percentage': friendly_percentage,
            'enemy_percentage': enemy_percentage,
            'friendly_attacks_used': friendly_attacks_used,
            'enemy_attacks_used': enemy_attacks_used,
            'war_size': war_size,
            'prep_day_start': prep_day_start,
            'war_day_start': war_day_start,
            'war_day_end': war_day_end,
        }
        key = friendly_tag + enemy_tag + str(prep_day_start)
        expected_results[key] = war_data

        fetched_data_processor.add_or_update_war_to_db(**war_data)

    for war_entry_key in expected_results:
        war_entry = expected_results[war_entry_key]
        friendly_tag, enemy_tag, result, friendly_stars, enemy_stars, friendly_percentage, enemy_percentage, friendly_attacks_used, enemy_attacks_used, war_size, prep_day_start, war_day_start, war_day_end = war_entry.values()
        war_instance = test_db_session.query(WAR).filter_by(prep_day_start=prep_day_start, friendly_tag=friendly_tag, enemy_tag=enemy_tag).first()
        assert friendly_tag == war_instance.friendly_tag
        assert enemy_tag == war_instance.enemy_tag
        assert result == war_instance.result
        assert friendly_stars == war_instance.friendly_stars
        assert enemy_stars == war_instance.enemy_stars
        assert friendly_percentage == war_instance.friendly_percentage
        assert enemy_percentage == war_instance.enemy_percentage
        assert friendly_attacks_used == war_instance.friendly_attacks_used
        assert enemy_attacks_used == war_instance.enemy_attacks_used
        assert war_size == war_instance.war_size
        assert prep_day_start == war_instance.prep_day_start
        assert war_day_start == war_instance.war_day_start
        assert war_day_end == war_instance.war_day_end



@pytest.mark.parametrize('timestamps_to_add', [
    [
        100,
    ],
    [
        100,
        200,
    ],
    [
        100,
        100,
        200,
    ],
])
def test_add_scanned_data_time_to_db(test_db_session, fetched_data_processor, timestamps_to_add):
    expected_results = []
    for timestamp_to_add in timestamps_to_add:
        if timestamp_to_add not in expected_results:
            expected_results.append(timestamp_to_add)
        fetched_data_processor.add_scanned_data_time_to_db(timestamp_to_add)

    scanned_data_times = test_db_session.query(SCANNEDDATATIME).all()
    assert len(scanned_data_times) == len(expected_results)
    for scanned_data_time in scanned_data_times:
        index = scanned_data_time.scanned_data_index
        time = scanned_data_time.time
        assert expected_results[index-1] == time


@pytest.mark.parametrize('data_entries', [
    [
        (112, '#aewgiwa', 125, 638, 29236, 234824, 43950, 12, 10, 12),
    ],
    [
        (111, '#aewgiwa', 12, 15, 35, 105, 3490, 12, 3, 4),
        (114, '#aroigar', 34, 835, 123, 9458, 12340, 356, 5, 10),
    ],
    [
        (122, '#aewgiwa', 1230, 23, 65, 12345, 800, 10, 0, 10),
        (122, '#aroigar', 123, 45, 2345, 654634, 1000, 4, 7, 6),
        (200, '#aewgiwa', 1240, 1235, 68, 12352, 820, 11, 11, 11),
    ],
])
def test_add_scanned_data_to_db(test_db_session, fetched_data_processor, data_entries):
    expected_results_time = []
    for entry in data_entries:

        data_time, member_tag, troops_donated_monthly, troops_received_monthly, spells_donated_achievement, troops_donated_achievement, clan_games_points_achievement, attacks_won, defenses_won, town_hall_level = entry

        if data_time not in expected_results_time:
            if len(expected_results_time) > 0 and data_time < expected_results_time[-1]:
                print('Data must be entered sequentially. This showing means your test data is bad!!')
                assert False
            expected_results_time.append(data_time)
        index = expected_results_time.index(data_time) + 1

        scanned_data_kwargs = {
            'scanned_data_index': index,
            'member_tag': member_tag,
            'troops_donated_monthly': troops_donated_monthly,
            'troops_received_monthly': troops_received_monthly,
            'spells_donated_achievement': spells_donated_achievement,
            'troops_donated_achievement':  troops_donated_achievement,
            'clan_games_points_achievement': clan_games_points_achievement,
            'attacks_won': attacks_won,
            'defenses_won': defenses_won,
            'town_hall_level': town_hall_level,
        }

        # need this to not fail foreign constraint checks
        member_kwargs = {
            'member_tag': member_tag,
            'member_name': 'some name',
            'role': 'admin',
            'trophies': 0,
            'town_hall_level': 1,
            'in_clan_currently': True,
            'last_updated_time': data_time-1,
        }
        fetched_data_processor.add_scanned_data_time_to_db(data_time)
        # always say this data was newer than the data being inserted
        fetched_data_processor.add_or_update_member_in_db(data_time, **member_kwargs)

        fetched_data_processor.add_or_update_scanned_data_in_db(**scanned_data_kwargs)

    scanned_data_time_instances = test_db_session.query(SCANNEDDATATIME).all()
    assert len(scanned_data_time_instances) == len(expected_results_time)
    for scanned_data_time_instance in scanned_data_time_instances:
        data_time_at_index = expected_results_time[scanned_data_time_instance.scanned_data_index-1]
        assert scanned_data_time_instance.time == data_time_at_index

    for entry in data_entries:
        data_time, member_tag, troops_donated_monthly, troops_received_monthly, spells_donated_achievement, troops_donated_achievement, clan_games_points_achievement, attacks_won, defenses_won, town_hall_level = entry
        data_index_for_data_time = test_db_session.query(SCANNEDDATATIME).filter_by(time=data_time).first().scanned_data_index

        scanned_data_instance = test_db_session.query(SCANNEDDATA).filter_by(member_tag=member_tag, scanned_data_index=data_index_for_data_time).first()

        assert scanned_data_instance.member_tag == member_tag
        assert scanned_data_instance.scanned_data_index == data_index_for_data_time
        assert scanned_data_instance.troops_donated_monthly == troops_donated_monthly
        assert scanned_data_instance.troops_received_monthly == troops_received_monthly
        assert scanned_data_instance.spells_donated_achievement == spells_donated_achievement
        assert scanned_data_instance.troops_donated_achievement == troops_donated_achievement
        assert scanned_data_instance.clan_games_points_achievement == clan_games_points_achievement
        assert scanned_data_instance.attacks_won == attacks_won
        assert scanned_data_instance.defenses_won == defenses_won
        assert scanned_data_instance.town_hall_level == town_hall_level


@pytest.mark.skip(reason="Need to patch the last processed time and data directories")
def test_save_data_executes(test_db_session, fetched_data_processor):
    with mock.patch('ClashBot.FetchedDataProcessor.process_player_achievement_files', autospec=True) as process_player_achievement_files, \
            mock.patch('ClashBot.FetchedDataProcessor.process_clan_war_details_files', autospec=True) as process_clan_war_files_details:
        fetched_data_processor.save_data_files(657, "some_dir")
        process_player_achievement_files.assert_called_once_with(fetched_data_processor, test_db_session, 657, "some_dir")
        process_clan_war_files_details.assert_called_once_with(fetched_data_processor, test_db_session, 657, "some_dir")


@pytest.mark.skip(reason="Need to patch the last processed time and data directories")
def test_process_player_achievement_files_throws(test_db_session, fetched_data_processor):
    with pytest.raises(FileNotFoundError):
        fetched_data_processor.process_player_achievement_files(1234, "rand_dir")


@pytest.mark.skip(reason="Need to patch the last processed time and data directories")
def test_process_player_achievement_files_processes_file(test_db_session, fetched_data_processor):
    fake_data_for_this_test = test_fetched_data_processor_fake_data.get_data_for_test_process_player_achievement_files_processes_file()
    with mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(fake_data_for_this_test))) as mock_file, \
        mock.patch('ClashBot.FetchedDataProcessor.process_player_achievements', autospec=True) as process_player_achievements:
            # this time here is used to check for files (1 per day since that time in epoch).
            # Usually if a file does not exist it is skipped, but since we are mocking the file reads,
            # open() is ALWAYS successful so this has the potential to be slow if we use the default 0
            fetched_data_processor.process_player_achievement_files(1537945719, "rand_dir")
            expected_calls = []
            for player_achievements_entry in fake_data_for_this_test:
                expected_calls.append(mock.call(fetched_data_processor, test_db_session, player_achievements_entry))
            process_player_achievements.assert_has_calls(expected_calls)


@pytest.mark.skip(reason="Need to patch the last processed time and data directories")
def test_process_clan_war_details_files_throws(fetched_data_processor):
    with pytest.raises(FileNotFoundError):
        fetched_data_processor.process_clan_war_details_files(1234, "rand_dir")


@pytest.mark.skip(reason="Need to patch the last processed time and data directories")
def test_process_clan_war_details_files_processes_file(fetched_data_processor):
    fake_data_for_this_test = test_fetched_data_processor_fake_data.get_data_for_test_process_clan_war_details_files_processes_file()
    with mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(fake_data_for_this_test))) as mock_file, \
            mock.patch('ClashBot.FetchedDataProcessor.process_clan_war_details', autospec=True) as process_clan_war_details:
            # this time here is used to check for files (1 per day since that time in epoch).
            # Usually if a file does not exist it is skipped, but since we are mocking the file reads,
            # open() is ALWAYS successful so this has the potential to be slow if we use the default 0
            fetched_data_processor.process_clan_war_details_files(test_db_session, 1537945719, "rand_dir")
            expected_calls = []
            for clan_war_entry in fake_data_for_this_test:
                expected_calls.append(mock.call(fetched_data_processor, clan_war_entry))
            process_clan_war_details.assert_has_calls(expected_calls)


@pytest.mark.skip(reason="Still implementing")
def test_process_player_achievements(test_db_session, fetched_data_processor):
    """
    When process_player_achievements is called, these should be called:
    1 x add_scanned_data_time
    num_players x add_scanned_data
    num_players x add_clan
    num_players x add_account_name
    num_players x add_member
    """
    # need to add data here
    fake_achievements_entry = []
    with mock.patch('ClashBot.FetchedDataProcessor.add_scanned_data_time_to_db', autospec=True) as add_scanned_data_time_to_db, \
        mock.patch('ClashBot.FetchedDataProcessor.add_or_update_scanned_data_in_db', autospec=True) as add_scanned_data_to_db, \
        mock.patch('ClashBot.FetchedDataProcessor.add_clan_to_db', autospec=True) as add_clan_to_db, \
        mock.patch('ClashBot.FetchedDataProcessor.add_account_name_to_db', autospec=True) as add_account_name_to_db, \
        mock.patch('ClashBot.FetchedDataProcessor.add_or_update_member_in_db', autospec=True) as add_member_to_db:
            fetched_data_processor.process_player_achievements(fake_achievements_entry)
            add_scanned_data_time_to_db.assert_called_once_with()
            expected_calls_add_scanned_data_to_db = []
            expected_calls_add_clan_to_db = []
            expected_calls_add_account_name_to_db = []
            expected_calls_add_member_to_db = []
            for member_achievements_entry in fake_achievements_entry:
                # need to add data here
                expected_calls_add_scanned_data_to_db.append()
                expected_calls_add_clan_to_db.append()
                expected_calls_add_account_name_to_db.append()
                expected_calls_add_member_to_db.append()
            add_scanned_data_time_to_db.assert_called_once_with()
            add_scanned_data_to_db.assert_has_calls(expected_calls_add_scanned_data_to_db)
            add_clan_to_db.assert_has_calls(expected_calls_add_clan_to_db)
            add_account_name_to_db.assert_has_calls(expected_calls_add_account_name_to_db)
            add_member_to_db.assert_has_calls(expected_calls_add_member_to_db)
