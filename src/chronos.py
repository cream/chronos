#!/usr/bin/env python

from gi.repository import GObject as gobject

import cream
import cream.ipc
import cream.util

from cream.util.dicts import ordereddict

from chronos.ui import CalendarUI
from chronos.event import Event

from chronos.ui.utils import find_colors


class Chronos(cream.Module):

    def __init__(self):

        cream.Module.__init__(self, 'org.cream.Chronos')

        self.events = {}
        self.calendars = ordereddict()
        self.colors = find_colors(.57, .72, .79)

        self.calendar = cream.ipc.get_object('org.cream.PIM', '/org/cream/PIM/Calendar')
        self.calendar.search_for_calendars()

        self.calendar.connect_to_signal('calendar_added', self.add_calendar)
        self.calendar.connect_to_signal('event_added', self.add_event)
        self.calendar.connect_to_signal('event_removed', self.remove_event)
        self.calendar.connect_to_signal('event_updated', self.update_event)

        self.calendar_ui = CalendarUI()

        self.calendar_ui.window.connect('delete_event', lambda *x: self.quit())
        self.calendar_ui.connect('calendar-state-changed', self.calendar_state_change_cb)


        for calendar in self.calendar.get_calendars():
            self.add_calendar(calendar['uid'], calendar)

        def add_events():
            events = self.calendar.query({})
            self.add_events(events)
        gobject.timeout_add(1, add_events)


    def add_event(self, uid, event):

        color = self.calendars[event['calendar_uid']]['color']

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

        color = self.colors.next()

        calendar.update({'color': color, 'active': True})
        self.calendars[calendar['uid']] = calendar

        new = ordereddict()
        for key in sorted(self.calendars, key=lambda k: self.calendars[k]['name']):
            new[key] = self.calendars[key]

        self.calendars = new

        self.calendar_ui.set_calendars(self.calendars.values())


    def calendar_state_change_cb(self, ui, uid, state):

        self.calendars[uid]['active'] = state

        for event in self.events.itervalues():
            if event.calendar_uid == uid:
                event.active = state
                self.calendar_ui.update_event(event)



if __name__ == '__main__':
    cream.util.set_process_name('chronos')
    chronos = Chronos()
    chronos.main()
