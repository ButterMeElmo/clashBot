import pytest
import pytz
import datetime

@pytest.fixture(scope='function')
def patch_datetime_now(monkeypatch, request):

	class mydatetime(datetime.datetime):

		@classmethod
		def utcnow(cls):
			return request.param
	
	monkeypatch.setattr(datetime, 'datetime', mydatetime)
