import datetime
import pytz
import time

class DateFetcherFormatter:

    def getUTCDateTime(self):
        date = datetime.datetime.utcnow()
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)
        return counter_aware_utc_dt

    def getUTCTimestamp(self):
        return int(self.getUTCDateTime().timestamp())

    def getPrettyTimeStringFromUTCTimestamp(self, timestamp):
        date = datetime.datetime.utcfromtimestamp(timestamp)
        counter_aware_utc_dt = date.replace(tzinfo=pytz.utc)
        return str(counter_aware_utc_dt)
