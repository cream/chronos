from chronos.utils import datetime

class Event(object):
    """An internal representation of an event."""

    def __init__(self, uid=None,
                       title='',
                       description='',
                       start=None,
                       end=None,
                       location=None,
                       calendar_uid=None):

        self.uid = uid
        self.title = title
        self.description = description
        self.start = start
        self.end = end
        self.location = location
        self.calendar_uid = calendar_uid

        if isinstance(start, (float, int)):
            self.start = datetime.fromtimestamp(start)
        if isinstance(end, (float, int)):
            self.end = datetime.fromtimestamp(end)


    def __eq__(self, other):

        if (self.uid == other.uid and
           self.title == other.title and
           self.description == other.description and
           self.start == other.start and
           self.end == other.end and
           self.location == other.location and
           self.calendar_uid == other.calendar_uid):
            return True
        else:
            return False


    def __ne__(self, other):
        return not self.__eq__(other)
