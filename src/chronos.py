#!/usr/bin/env python

import cream
import cream.ipc
import cream.util

from chronos.ui import CalendarUI
from chronos.event import Event


class Chronos(cream.Module):

    def __init__(self):
    
        cream.Module.__init__(self, 'org.cream.Chronos')
        
        self.events = {}
        self.calendar_colors = {}

        self.calendar = cream.ipc.get_object('org.cream.PIM', '/org/cream/PIM/Calendar')
        self.calendar.search_for_calendars()
        
        self.calendar.connect_to_signal('calendar_added', self.add_calendar)
        self.calendar.connect_to_signal('event_added', self.add_event)
        self.calendar.connect_to_signal('event_removed', self.remove_event)
        self.calendar.connect_to_signal('event_updated', self.update_event)
    
        self.calendar_ui = CalendarUI()
        
        self.calendar_ui.window.connect('delete_event', lambda *x: self.quit())

        
        for calendar in self.calendar.get_calendars():
            self.add_calendar(calendar['uid'], calendar)

        for event in self.calendar.query({}):
            self.add_event(event['uid'], event)
        
    def add_event(self, uid, event):

        color = self.calendar_colors[event.pop('calendar_uid')]
        
        event = Event(color=color, **event)
        self.events[uid] = event

        self.calendar_ui.add_event(event)
        
        
    def remove_event(self, uid, event):

        self.events.pop(uid)

        self.calendar_ui.main_view.remove_event(event)


    def update_event(self, uid, event):

        event = Event(**event)
        self.events[uid] = event

        self.calendar_ui.main_view.update_event(event)


    def add_calendar(self, uid, calendar):

        color = self.calendar_ui.add_calendar(calendar)

        self.calendar_colors[calendar['uid']] = color



if __name__ == '__main__':
    cream.util.set_process_name('chronos')
    chronos = Chronos()
    chronos.main()
