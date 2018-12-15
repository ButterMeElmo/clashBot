import datetime
import pytest
import pytz
from unittest import mock
from ClashBot import DateFetcherFormatter
# pylint: disable=unused-import
from helper_for_testing import patch_datetime_now
# pylint: enable=unused-import 

@pytest.fixture
def date_fetcher_formatter():
    """
    This is a fixture for use in all tests in the module.
    """
    return DateFetcherFormatter()

FAKE_TIME = datetime.datetime(2025, 12, 25, 1, 5, 55)
@pytest.mark.parametrize('patch_datetime_now', [FAKE_TIME], indirect=True)
# pylint: disable=redefined-outer-name,unused-argument
def test_get_utc_datetime(patch_datetime_now, date_fetcher_formatter):
    # pylint: enable=redefined-outer-name,unused-argument
    """
    This tests the get_utc_datetime method of DateFetcherFormatter.
    That function is used widely, so this test is particularly important.
    """
    desired_datetime = datetime.datetime(2025, 12, 25, 1, 5, 55, tzinfo=pytz.utc)
    calculated_datetime = date_fetcher_formatter.get_utc_date_time()
    assert desired_datetime == calculated_datetime

    desired_timestamp = 1766624755
    assert desired_timestamp == calculated_datetime.timestamp()

@pytest.mark.parametrize('date_to_test, expected_output', [
    (datetime.datetime(2014, 6, 2, 1, 6, 15, tzinfo=pytz.utc), 1401671175),
    (datetime.datetime(2030, 12, 9, 6, 12, 46, tzinfo=pytz.utc), 1923027166)
])
# pylint: disable=redefined-outer-name
def test_basic_get_utc_timestamp(date_fetcher_formatter, date_to_test, expected_output):
    # pylint: enable=redefined-outer-name
    """
    This tests the get_utc_timestamp method of DateFetcherFormatter with hand calculated output.
    """
    with mock.patch('ClashBot.DateFetcherFormatter.get_utc_date_time', return_value=date_to_test):
        assert date_fetcher_formatter.get_utc_timestamp() == expected_output

@pytest.mark.parametrize('date_to_test', [
    datetime.datetime(2014, 6, 2, 1, 6, 15, tzinfo=pytz.utc),
    datetime.datetime(2030, 12, 9, 6, 12, 46, tzinfo=pytz.utc)
])
# pylint: disable=redefined-outer-name
def test_get_utc_timestamp(date_fetcher_formatter, date_to_test):
    # pylint: enable=redefined-outer-name
    """
    This tests the get_utc_timestamp method of DateFetcherFormatter.
    """
    with mock.patch('ClashBot.DateFetcherFormatter.get_utc_date_time', return_value=date_to_test):
        assert date_fetcher_formatter.get_utc_timestamp() == int(date_to_test.timestamp())

@pytest.mark.parametrize('date_to_test, timestamp, expected_output', [
    (datetime.datetime(2014, 6, 2, 1, 6, 15, tzinfo=pytz.utc), 1401671175, '2014-06-02 01:06:15+00:00')
])
# pylint: disable=redefined-outer-name
def test_basic_turn_utc_timestamp_into_string(date_fetcher_formatter, date_to_test, timestamp, expected_output):
    # pylint: enable=redefined-outer-name
    """
    This tests the get_pretty_time_string_from_utc_timestamp method of DateFetcherFormatter with hand calculated outputs.
    """
    with mock.patch('ClashBot.DateFetcherFormatter.get_utc_date_time', return_value=date_to_test):
        assert date_fetcher_formatter.get_pretty_time_string_from_utc_timestamp(timestamp) == expected_output

@pytest.mark.parametrize('date_to_test', [
    datetime.datetime(2014, 6, 2, 1, 6, 15, tzinfo=pytz.utc),
    datetime.datetime(2030, 12, 9, 6, 12, 46, tzinfo=pytz.utc)
])
# pylint: disable=redefined-outer-name
def test_turn_utc_timestamp_into_string(date_fetcher_formatter, date_to_test):
    # pylint: enable=redefined-outer-name
    """
    This tests the get_pretty_time_string_from_utc_timestamp method of DateFetcherFormatter.
    """
    with mock.patch('ClashBot.DateFetcherFormatter.get_utc_date_time', return_value=date_to_test):
        desired_results = str(datetime.datetime.utcfromtimestamp(date_to_test.timestamp()).replace(tzinfo=pytz.utc))
        assert date_fetcher_formatter.get_pretty_time_string_from_utc_timestamp(date_to_test.timestamp()) == desired_results
