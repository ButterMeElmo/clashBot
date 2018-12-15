import datetime
import pytz


class DateFetcherFormatter:

    @staticmethod
    def get_utc_date_time():
        date = datetime.datetime.utcnow()
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)
        return counter_aware_utc_dt

    @staticmethod
    def get_utc_timestamp():
        return int(DateFetcherFormatter.get_utc_date_time().timestamp())

    @staticmethod
    def get_pretty_time_string_from_utc_timestamp(timestamp):
        date = datetime.datetime.utcfromtimestamp(timestamp)
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)
        return str(counter_aware_utc_dt)
