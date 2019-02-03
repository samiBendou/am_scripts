from datetime import timedelta
from datetime import datetime


class DateBase:
    day = {"day": 1, "week": 7, "month": 30, "year": 365}

    def __init__(self, covered=0, date=None, period=None, offset=None, start=None, end=None):
        self.covered = None
        self.date = None
        self.raw_start = None
        self.period = None
        self.offset = None
        self.start = None
        self.end = None
        self.range = None
        if date is not None and covered > 0:
            self.reset(date, covered)
            self.set(period, offset, start, end)

    def reset(self, date=None, covered=None):
        self.date = self.date if date is None else date
        self.covered = self.covered if covered is None else covered
        self.raw_start = self.date - timedelta(days=self.covered - 1)
        self.set()

    def set(self, period=None, offset=None, start=None, end=None):
        self.period = period
        self.offset = offset
        self.start = start
        self.end = end
        (self.period, self.offset, self.start, self.end) = self._unwrap()
        self.range = int((self.end - self.start) / self.period - self.offset) + 1

    def _unwrap(self):
        assert self.date is not None and self.covered > 0

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
            delta = self.start - self.raw_start
            add_day = 1 if ((delta - timedelta(days=delta.days)) + self.raw_start).day != self.raw_start.day else 0
            return int(delta.days + add_day)

    def _unwrap_end(self):
        if self.end is None:
            return self.covered - 1
        elif type(self.end) is int:
            return self.end
        elif type(self.end) is datetime:
            return (self.date - self.raw_start).days + 1
