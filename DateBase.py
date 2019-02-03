from datetime import timedelta
from datetime import datetime


class DateBase:
    day = {"day": 1, "week": 7, "month": 30, "year": 365}

    def __init__(self, covered=0, date=None, period=None, offset=None, start=None, end=None):
        self.period = None
        self.offset = None
        self.start = None
        self.end = None
        self.covered = covered
        self.date = date
        self.range = 0

        if date is not None and self.covered > 0:
            self.set(period, offset, start, end)

    def set(self, period=None, offset=None, start=None, end=None):
        assert self.date is not None and self.covered > 0

        self.period = period
        self.offset = offset
        self.start = start
        self.end = end
        (self.period, self.offset, self.start, self.end) = self._unwrap()
        self.range = int((self.end - self.start) / self.period - self.offset) + 1

    def _unwrap(self):
        period = self._unwrap_period()
        offset = self._unwrap_offset()
        start = self._unwrap_start()
        end = self._unwrap_end()

        assert end - start <= self.covered
        return period, offset, start, end

    def _unwrap_period(self):
        if self.period is None:
            return 1
        elif type(self.period) is int:
            return self.period
        elif type(self.period) is str:
            try:
                return DateBase.day[self.period]
            except KeyError:
                raise NotImplementedError

    def _unwrap_offset(self):
        return 0 if self.offset is None else int(self.offset)

    def _unwrap_start(self):
        if self.start is None:
            return 0
        elif type(self.start) is int:
            return self.start
        elif type(self.start) is datetime:
            raw_start = (self.date - timedelta(days=self.covered - 1))
            d_start = self.start
            delta = d_start - raw_start
            add_day = 1 if ((delta - timedelta(days=delta.days)) + raw_start).day != raw_start.day else 0
            return int(delta.days + add_day)

    def _unwrap_end(self):
        if type(self.end) is int:
            return self.end
        elif type(self.end) is datetime:
            raw_start = (self.date - timedelta(days=self.covered - 1))
            d_end = self.date if self.end is None else self.end
            return (d_end - raw_start).days + 1
        elif self.end is None:
            return self.covered - 1
