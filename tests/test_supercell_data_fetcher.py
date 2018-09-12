# pylint: disable=line-too-long
"""
This is the module for testing SupercellDataFetcher, which is responsible for getting the data from the Supercell servers.
"""
import datetime
from unittest import mock
import pytest
import pytz
from clashBot import SupercellDataFetcher
# pylint: disable=unused-import
from helper_for_testing import patch_datetime_now
# pylint: enable=unused-import

@pytest.fixture
def data_fetcher():
    """
e   This is a fixture for use in all tests in the module.
    """
    return SupercellDataFetcher()

# pylint: disable=redefined-outer-name
def test_get_file_name(data_fetcher):
    """
    This tests the get_file_name method of SupercellDataFetcher.
    """
    date_to_test = datetime.datetime(2020, 12, 25, 1, 5, 55, tzinfo=pytz.utc)
    with mock.patch('clashBot.SupercellDataFetcher.getUTCDateTime', return_value=date_to_test):
        assert data_fetcher.getFileName('something', '.json') == 'something_2020-12-25.json'

    date_to_test_2 = datetime.datetime(2012, 11, 5, 11, 15, 5, tzinfo=pytz.utc)
    assert data_fetcher.getFileName('something', '.json', date_to_test_2) == 'something_2012-11-5.json'
# pylint: enable=redefined-outer-name


# pylint: disable=redefined-outer-name
def test_get_file_names(data_fetcher):
    """
    This tests the get_file_names method of SupercellDataFetcher.
    """
    date_to_test = datetime.datetime(2020, 12, 25, 1, 5, 55, tzinfo=pytz.utc)
    with mock.patch('clashBot.SupercellDataFetcher.getUTCDateTime', return_value=date_to_test):
        starting_timestamp = date_to_test - datetime.timedelta(days=3)
        starting_timestamp = int(starting_timestamp.timestamp())
        desired_results = [
            'something_2020-12-22.json',
            'something_2020-12-23.json',
            'something_2020-12-24.json',
            'something_2020-12-25.json'
            ]
        assert data_fetcher.getFileNames('something', '.json', starting_timestamp) == desired_results
# pylint: enable=redefined-outer-name

FAKE_TIME = datetime.datetime(2025, 12, 25, 1, 5, 55)
@pytest.mark.parametrize('patch_datetime_now', [FAKE_TIME], indirect=True)
# pylint: disable=redefined-outer-name,unused-argument
def test_get_utc_datetime(patch_datetime_now, data_fetcher):
    # pylint: enable=redefined-outer-name,unused-argument
    """
    This tests the get_utc_datetime method of SupercellDataFetcher.
    That function is used widely, so this test is particularly important.
    """
    desired_datetime = datetime.datetime(2025, 12, 25, 1, 5, 55, tzinfo=pytz.utc)
    calculated_datetime = data_fetcher.getUTCDateTime()
    assert desired_datetime == calculated_datetime

    desired_timestamp = 1766624755
    assert desired_timestamp == calculated_datetime.timestamp()

@pytest.mark.parametrize('date_to_test, expected_output', [
    (datetime.datetime(2014, 6, 2, 1, 6, 15, tzinfo=pytz.utc), 1401671175),
    (datetime.datetime(2030, 12, 9, 6, 12, 46, tzinfo=pytz.utc), 1923027166)
])
# pylint: disable=redefined-outer-name
def test_basic_get_utc_timestamp(data_fetcher, date_to_test, expected_output):
    # pylint: enable=redefined-outer-name
    """
    This tests the get_utc_timestamp method of SupercellDataFetcher with hand calculated output.
    """
    with mock.patch('clashBot.SupercellDataFetcher.getUTCDateTime', return_value=date_to_test):
        assert data_fetcher.getUTCTimestamp() == expected_output

@pytest.mark.parametrize('date_to_test', [
    datetime.datetime(2014, 6, 2, 1, 6, 15, tzinfo=pytz.utc),
    datetime.datetime(2030, 12, 9, 6, 12, 46, tzinfo=pytz.utc)
])
# pylint: disable=redefined-outer-name
def test_get_utc_timestamp(data_fetcher, date_to_test):
    # pylint: enable=redefined-outer-name
    """
    This tests the get_utc_timestamp method of SupercellDataFetcher.
    """
    with mock.patch('clashBot.SupercellDataFetcher.getUTCDateTime', return_value=date_to_test):
        assert data_fetcher.getUTCTimestamp() == int(date_to_test.timestamp())

@pytest.mark.parametrize('date_to_test, timestamp, expected_output', [
    (datetime.datetime(2014, 6, 2, 1, 6, 15, tzinfo=pytz.utc), 1401671175, '2014-06-02 01:06:15+00:00')
])
# pylint: disable=redefined-outer-name
def test_basic_turn_utc_timestamp_into_string(data_fetcher, date_to_test, timestamp, expected_output):
    # pylint: enable=redefined-outer-name
    """
    This tests the get_pretty_time_string_from_utc_timestamp method of SupercellDataFetcher with hand calculated outputs.
    """
    with mock.patch('clashBot.SupercellDataFetcher.getUTCDateTime', return_value=date_to_test):
        assert data_fetcher.getPrettyTimeStringFromUTCTimestamp(timestamp) == expected_output

@pytest.mark.parametrize('date_to_test', [
    datetime.datetime(2014, 6, 2, 1, 6, 15, tzinfo=pytz.utc),
    datetime.datetime(2030, 12, 9, 6, 12, 46, tzinfo=pytz.utc)
])
# pylint: disable=redefined-outer-name
def test_turn_utc_timestamp_into_string(data_fetcher, date_to_test):
    # pylint: enable=redefined-outer-name
    """
    This tests the get_pretty_time_string_from_utc_timestamp method of SupercellDataFetcher.
    """
    with mock.patch('clashBot.SupercellDataFetcher.getUTCDateTime', return_value=date_to_test):
        desired_results = str(datetime.datetime.utcfromtimestamp(date_to_test.timestamp()).replace(tzinfo=pytz.utc))
        assert data_fetcher.getPrettyTimeStringFromUTCTimestamp(date_to_test.timestamp()) == desired_results

@pytest.mark.skip(reason="waiting to implement ACTUALLY getting data from server")
# pylint: disable=redefined-outer-name
def test_get_data_from_server():
    # pylint: enable=redefined-outer-name
    """
    Once implemented, this will test that we successfully get data from the supercell servers.
    """
    assert False

# pylint: disable=redefined-outer-name
def test_validate_data(data_fetcher, tmpdir):
    """
    This opens the saved data files and verifies they are updated and valid.
    Valid doesn't mean perfect, it just means it has the timestamp and seemsd to have been pulled.
    More in depth validity checking occurs when parseing data into the DB.
    """
    date_to_test = datetime.datetime(2020, 12, 25, 1, 5, 55, tzinfo=pytz.utc)
    with mock.patch('clashBot.SupercellDataFetcher.getUTCDateTime', return_value=date_to_test):

        # test no files
        assert data_fetcher.validateData(tmpdir) is False

        # test empty files
        tmpdir.join(data_fetcher.getFileName('warDetailsLog', '.json')).write('')
        tmpdir.join(data_fetcher.getFileName('clanLog', '.json')).write('')
        tmpdir.join(data_fetcher.getFileName('warLog', '.json')).write('')
        tmpdir.join(data_fetcher.getFileName('clanPlayerAchievements', '.json')).write('')
        assert data_fetcher.validateData(tmpdir) is False

        # test junk files
        tmpdir.join(data_fetcher.getFileName('warDetailsLog', '.json')).write('aiwgoiahgoawgh')
        tmpdir.join(data_fetcher.getFileName('clanLog', '.json')).write('aiwgoiahgoawgh')
        tmpdir.join(data_fetcher.getFileName('warLog', '.json')).write('aiwgoiahgoawgh')
        tmpdir.join(data_fetcher.getFileName('clanPlayerAchievements', '.json')).write('aiwgoiahgoawgh')
        assert data_fetcher.validateData(tmpdir) is False

        # test valid, but empty json
        tmpdir.join(data_fetcher.getFileName('warDetailsLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.getFileName('clanLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.getFileName('warLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.getFileName('clanPlayerAchievements', '.json')).write('{}')
        assert data_fetcher.validateData(tmpdir) is False

        # test valid json with not the correct key we look for
        tmpdir.join(data_fetcher.getFileName('warDetailsLog', '.json')).write('"a":{}')
        tmpdir.join(data_fetcher.getFileName('clanLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.getFileName('warLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.getFileName('clanPlayerAchievements', '.json')).write('{}')
        assert data_fetcher.validateData(tmpdir) is False

        # test valid everything
        timestamp_for_data = date_to_test.timestamp() * 1000
        data_to_write = '[{"timestamp":' + str(timestamp_for_data) + '}]'
        tmpdir.join(data_fetcher.getFileName('warDetailsLog', '.json')).write(data_to_write)
        tmpdir.join(data_fetcher.getFileName('clanLog', '.json')).write(data_to_write)
        tmpdir.join(data_fetcher.getFileName('warLog', '.json')).write(data_to_write)
        tmpdir.join(data_fetcher.getFileName('clanPlayerAchievements', '.json')).write(data_to_write)
        assert data_fetcher.validateData(tmpdir) is True
# pylint: enable=redefined-outer-name
