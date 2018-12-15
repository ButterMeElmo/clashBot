# pylint: disable=line-too-long
"""
This is the module for testing SupercellDataFetcher, which is responsible for getting the data from the Supercell servers.
"""
import datetime
from unittest import mock
import pytest
import pytz
from ClashBot import SupercellDataFetcher

@pytest.fixture
def data_fetcher():
    """
    This is a fixture for use in all tests in the module.
    """
    return SupercellDataFetcher()

# pylint: disable=redefined-outer-name
def test_get_file_name(data_fetcher):
    """
    This tests the get_file_name method of SupercellDataFetcher.
    """
    date_to_test = datetime.datetime(2020, 12, 25, 1, 5, 55, tzinfo=pytz.utc)
    with mock.patch('ClashBot.DateFetcherFormatter.get_utc_date_time', return_value=date_to_test):
        assert data_fetcher.get_file_name('data', 'something', '.json') == 'data/something_2020-12-25.json'

    date_to_test_2 = datetime.datetime(2012, 11, 5, 11, 15, 5, tzinfo=pytz.utc)
    assert data_fetcher.get_file_name('data', 'something', '.json', date_to_test_2) == 'data/something_2012-11-5.json'
    assert data_fetcher.get_file_name('', 'something', '.json', date_to_test_2) == 'something_2012-11-5.json'
    assert data_fetcher.get_file_name('./', 'something', '.json', date_to_test_2) == './something_2012-11-5.json'
    assert data_fetcher.get_file_name('data/', 'something', '.json', date_to_test_2) == 'data/something_2012-11-5.json'
    assert data_fetcher.get_file_name('data\\', 'something', '.json', date_to_test_2) == 'data\\something_2012-11-5.json'
# pylint: enable=redefined-outer-name


# pylint: disable=redefined-outer-name
def test_get_file_names(data_fetcher):
    """
    This tests the get_file_names method of SupercellDataFetcher.
    """
    date_to_test = datetime.datetime(2020, 12, 25, 1, 5, 55, tzinfo=pytz.utc)
    with mock.patch('ClashBot.DateFetcherFormatter.get_utc_date_time', return_value=date_to_test):
        starting_timestamp = date_to_test - datetime.timedelta(days=3)
        starting_timestamp = int(starting_timestamp.timestamp())
        desired_results = [
            'data/something_2020-12-22.json',
            'data/something_2020-12-23.json',
            'data/something_2020-12-24.json',
            'data/something_2020-12-25.json'
            ]
        assert data_fetcher.get_file_names('data', 'something', '.json', starting_timestamp) == desired_results
# pylint: enable=redefined-outer-name

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
    with mock.patch('ClashBot.DateFetcherFormatter.get_utc_date_time', return_value=date_to_test):

        # test no files
        assert data_fetcher.validate_data(tmpdir) is False

        # test empty files
        tmpdir.join(data_fetcher.get_file_name('./', 'warDetailsLog', '.json')).write('')
        tmpdir.join(data_fetcher.get_file_name('./', 'clanLog', '.json')).write('')
        tmpdir.join(data_fetcher.get_file_name('./', 'warLog', '.json')).write('')
        tmpdir.join(data_fetcher.get_file_name('./', 'clanPlayerAchievements', '.json')).write('')
        assert data_fetcher.validate_data(tmpdir) is False

        # test junk files
        tmpdir.join(data_fetcher.get_file_name('./', 'warDetailsLog', '.json')).write('aiwgoiahgoawgh')
        tmpdir.join(data_fetcher.get_file_name('./', 'clanLog', '.json')).write('aiwgoiahgoawgh')
        tmpdir.join(data_fetcher.get_file_name('./', 'warLog', '.json')).write('aiwgoiahgoawgh')
        tmpdir.join(data_fetcher.get_file_name('./', 'clanPlayerAchievements', '.json')).write('aiwgoiahgoawgh')
        assert data_fetcher.validate_data(tmpdir) is False

        # test valid, but empty json
        tmpdir.join(data_fetcher.get_file_name('./', 'warDetailsLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.get_file_name('./', 'clanLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.get_file_name('./', 'warLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.get_file_name('./', 'clanPlayerAchievements', '.json')).write('{}')
        assert data_fetcher.validate_data(tmpdir) is False

        # test valid json with not the correct key we look for
        tmpdir.join(data_fetcher.get_file_name('./', 'warDetailsLog', '.json')).write('"a":{}')
        tmpdir.join(data_fetcher.get_file_name('./', 'clanLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.get_file_name('./', 'warLog', '.json')).write('{}')
        tmpdir.join(data_fetcher.get_file_name('./', 'clanPlayerAchievements', '.json')).write('{}')
        assert data_fetcher.validate_data(tmpdir) is False

        # test valid everything
        timestamp_for_data = date_to_test.timestamp() * 1000
        data_to_write = '[{"timestamp":' + str(timestamp_for_data) + '}]'
        tmpdir.join(data_fetcher.get_file_name('./', 'warDetailsLog', '.json')).write(data_to_write)
        tmpdir.join(data_fetcher.get_file_name('./', 'clanLog', '.json')).write(data_to_write)
        tmpdir.join(data_fetcher.get_file_name('./', 'warLog', '.json')).write(data_to_write)
        tmpdir.join(data_fetcher.get_file_name('./', 'clanPlayerAchievements', '.json')).write(data_to_write)
        assert data_fetcher.validate_data(tmpdir) is True
# pylint: enable=redefined-outer-name
