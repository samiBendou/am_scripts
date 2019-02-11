"""
Various tools classes for the project
"""

from datetime import timedelta
from datetime import datetime
import matplotlib.pyplot as plt


class DateBase:
    """
    Representation of a time period

    Provides a structure to represent data daily gathered at periodic date interval.

    Attributes:
        covered (int): Number of days covered by data
        raw_start: Real start date. Start of data
        date (datetime): Real end. End date of data
        period (int/str): Number of days contained in a period eg. period="week", period=12, ...
        offset (int): Offset from start date in number of periods
        start (datetime): Effective Start date. Must be coherent with data to represent
        end (datetime): Effective end date. Must be coherent with data to represent
        range (int): Number of periods to cover according to other attributes
    """

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
        """
        Resets DateBase with new data parameters

        Parameters:
            date (datetime): New real end of the data
            covered (int): New number of days covered
        """
        self.date = self.date if date is None else date
        self.covered = self.covered if covered is None else covered
        self.raw_start = self.date - timedelta(days=self.covered - 1)
        self.set()

    def set(self, period=None, offset=None, start=None, end=None):
        """Sets DateBase with new period parameters. See class documentation for more details"""
        self.period = period
        self.offset = offset
        self.start = start
        self.end = end
        (self.period, self.offset, self.start, self.end) = self._unwrap()
        self.range = int((self.end - self.start) / self.period - self.offset) + 1

    def list(self):
        """Returns a list of datetime objects representing the current DateBase state"""
        day = timedelta(days=1)
        x = [0] * self.range
        for k in range(0, self.range):
            shift = (k + self.offset) * self.period - self.covered + 1 + self.start
            x[k] = (self.date + shift * day)
        return x

    def start_date(self):
        """Returns effective datetime start"""
        return self.start * timedelta(days=1) + self.raw_start

    def end_date(self):
        """Return effective datetime end"""
        return self.end * timedelta(days=1) + self.raw_start

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


class GenericPlot:
    """
    Plotting static interface base class

    Used as interface with matplotlib for every result that can be computed with Data objects. Provides displays and
    save functions for any plot of the project.

    Attributes:
        save (bool): If true, aves the plots onto render/<plot_dir> when render() is called
        show (bool): If true, shows the plots when render() is called
    """

    RENDER_ROOT = "render/"
    save = True
    show = True

    @classmethod
    def render(cls, xl=None, yl=None, title=None, date=None, legend=True):
        """
        Generic plotting

        The plots behaves differently when changing cls.save and cls.show attributes.

        Parameters:
            xl (str): Label of x axis
            yl (str): Label of y axis
            title (str): Title of the plot
            date (datetime): Date of the plot. Used for file naming
            legend (bool): If true prints legend
        """
        dated_title = None

        if legend is True:
            plt.legend()

        if title is not None:
            dated_title = title + "" if date is None else date.strftime("%m-%d-%y") + " " + title
            plt.title(dated_title)

        if xl is not None:
            plt.xlabel(xl)

        if yl is not None:
            plt.ylabel(yl)

        if cls.save:
            filename = "untitled" if title is None else dated_title.replace(" ", "_").lower()
            plt.savefig(cls.RENDER_ROOT + filename)

        if cls.show:
            plt.show()

        plt.clf()


def get_enum_value():
    return lambda e: [list(map(lambda x: x.value, l)) for l in e]


enum_value = get_enum_value()
