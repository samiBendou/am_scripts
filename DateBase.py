from datetime import timedelta
from datetime import datetime


class DateBase:
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
        self.period = period
        self.offset = offset
        self.start = start
        self.end = end
        (self.period, self.offset, self.start, self.end) = self._unwrap()
        self.range = int((self.end - self.start) / self.period - self.offset) + 1

    def _unwrap(self):
        raw_start = (self.date - timedelta(days=self.covered - 1))
        d_start, d_end = datetime.now(), datetime.now()
        period = 1 if self.period is None else self.period
        offset = 0 if self.offset is None else self.offset

        ret = [period, offset]
        if type(self.start) is int:
            assert type(self.end) is int
            ret.append(self.start)
        else:
            d_start = raw_start if self.start is None else self.start
            delta = d_start - raw_start
            add_day = 1 if ((delta - timedelta(days=delta.days)) + raw_start).day != raw_start.day else 0
            ret.append(int(delta.days + add_day))

        if type(self.end) is int:
            assert type(self.start) is int
            ret.append(self.end)
        else:
            d_end = self.date if self.end is None else self.end
            ret.append((d_end - d_start).days + 1)

        assert ret[-1] - ret[-2] <= self.covered

        return tuple(ret)
