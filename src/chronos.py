#!/usr/bin/env python

import cream
import cream.ipc

from chronos.ui import CalendarUI
from chronos.event import Event


class Calendar(cream.Module):

    def __init__(self):
    
        cream.Module.__init__(self, 'org.cream.Calendar')
        
        self.events = {}

        self.calendar = cream.ipc.get_object('org.cream.PIM', '/org/cream/PIM/Calendar')
        self.calendar.search_for_calendars()
        
        self.calendar.connect_to_signal('calendar_added', self.add_calendar)
        self.calendar.connect_to_signal('event_added', self.add_event)
        self.calendar.connect_to_signal('event_removed', self.remove_event)
    
        self.calendar_ui = CalendarUI()
        
        self.calendar_ui.window.window.connect('delete_event', lambda *x: self.quit())

        
        for calendar in self.calendar.get_calendars():
            self.add_calendar(calendar['uid'], calendar)

        for event in self.calendar.query({}):
            self.add_event(event['uid'], event)
        
    def add_event(self, uid, event):
        
        event = Event(**event)
        self.events[uid] = event

        self.calendar_ui.main_view.add_event(event)
        
        
    def remove_event(self, uid, event):

        self.events.pop(uid)

        self.calendar_ui.main_view.remove_event(event)


    def on_event_updated(self, uid, event):
        pass
        
    def add_calendar(self, uid, calendar):
    
        self.calendar_ui.calendar_view.add_calendar(calendar)
        
        
        
        
if __name__ == '__main__':

    calendar = Calendar()
    calendar.main()
