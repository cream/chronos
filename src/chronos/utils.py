import calendar
import datetime as _datetime

from cream.util import flatten


class datetime(_datetime.datetime):

    def __init__(self, *args, **kwargs):

        _datetime.datetime.__init__(*args, **kwargs)


    @classmethod
    def from_date(cls, d):

        return cls(d.year, d.month, d.day)


    @property
    def as_date(self):

        return datetime(self.year, self.month, self.day)


    @property
    def next_month(self):

        if self.month == 12:
            year = self.year + 1
            month = 1
            day = self.day
            while day > days_in_month(year, month):
                day -= 1
        else:
            year = self.year
            month = self.month + 1
            day = self.day
            while day > days_in_month(year, month):
                day -= 1

        return datetime(year, month, day, self.hour, self.minute,
                         self.second, self.microsecond, self.tzinfo)


    @property
    def previous_month(self):

        if self.month == 1:
            year = self.year - 1
            month = 12
            day = self.day
            while day > days_in_month(year, month):
                day -= 1
        else:
            year = self.year
            month = self.month - 1
            day = self.day
            while day > days_in_month(year, month):
                day -= 1

        return datetime(year, month, day, self.hour, self.minute,
                         self.second, self.microsecond, self.tzinfo)


    @property
    def next_day(self):

        next = self + _datetime.timedelta(1)
        return datetime(next.year, next.month, next.day, next.hour, next.minute,
                        next.second, next.microsecond, next.tzinfo)



def days_in_month(year, month):
    """
    Returns how many days the given month has.
    """
    monthdays = calendar.monthcalendar(year, month)
    return len(filter(lambda x: x > 0, flatten(monthdays)))


def iter_month_dates(year, month):
    """
    Returns an iterator for one month and will iterate trough complete weeks.
    """
    monthdates = calendar.Calendar().itermonthdates(year, month)
    for monthday in monthdates:
        yield datetime.from_date(monthday)


def iter_date_range(start, end):
    """
    Returns an iterator which yields all dates between ``start`` and ``end``
    """
    yield start
    date = start
    while date.as_date != end.as_date:
        date = date.next_day
        yield date



def number_of_weeks(year, month):
    """Returns the number of weeks the given month has."""
    return len(calendar.Calendar().monthdatescalendar(year, month))



if __name__ == '__main__':
    d = datetime(2011, 3, 30)
    print d
    print d.previous_month()
