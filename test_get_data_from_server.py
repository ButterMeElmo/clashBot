import pytest
import getDataFromServer
import pytz
import datetime
from helper_for_testing import patch_datetime_now

FAKE_TIME = datetime.datetime(2020, 12, 25, 1, 5, 55)

@pytest.mark.parametrize('patch_datetime_now', [FAKE_TIME], indirect=True)
def test_getFileName(patch_datetime_now):
	assert getDataFromServer.getFileName('something','.json') == 'something_2020-12-25.json'
	assert getDataFromServer.getFileName('something','.json', FAKE_TIME) == 'something_2020-12-25.json'

@pytest.mark.parametrize('patch_datetime_now', [FAKE_TIME], indirect=True)
def test_getFileNames(patch_datetime_now):
	starting_timestamp = int(datetime.datetime.utcnow().replace(day=FAKE_TIME.day-3).timestamp())
	desired_results = [
			'something_2020-12-22.json',
			'something_2020-12-23.json',
			'something_2020-12-24.json',
			'something_2020-12-25.json'
			]
	assert getDataFromServer.getFileNames('something', '.json', starting_timestamp) == desired_results
