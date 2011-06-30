import os
from gi.repository import Gtk as gtk, GObject as gobject

from chronos.ui.month import MonthView
from chronos.ui.day import DayView
from chronos.ui.tag import Tag

from chronos.utils import datetime

MONTH_YEAR_TEMPLATE = '<span weight="bold" size="x-large">%B %Y</span>'


class CalendarUI(gobject.GObject):

    __gsignals__ = {
        'calendar-state-changed': (gobject.SignalFlags.RUN_LAST, None, (str, bool)),
    }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.date = datetime.now()

        interface_path = os.path.join(os.path.dirname(__file__), 'calendar.ui')

        # Load the interface data
        self.interface = gtk.Builder()
        self.interface.add_from_file(interface_path)

        # Retrieve the objects being used here
        self.window = self.interface.get_object('main_window')
        self.layout = self.interface.get_object('layout')
        self.paned = self.interface.get_object('paned')
        self.month_year_label = self.interface.get_object('month_year')
        self.button_previous = self.interface.get_object('button_previous')
        self.button_next = self.interface.get_object('button_next')

        # Set the current year and month
        self.month_year_label.set_markup(self.date.strftime(MONTH_YEAR_TEMPLATE))

        # Construct the custom interfaces
        self.month_view = MonthView(self.date)
        self.day_view = DayView()

        # Connect the signals
        self.button_previous.connect('clicked', self.month_change_cb)
        self.button_next.connect('clicked', self.month_change_cb)

        # TODO: Make use of MonthViews signals!

        self.paned.add1(self.month_view)
        self.paned.add2(self.day_view)

        # Display the calendars as tags
        self.calendars = gtk.HBox()
        self.calendars.set_spacing(1)
        self.layout.pack_start(self.calendars, False, False, 0)

        # Show the window
        self.window.show_all()


    def set_date(self, date):

        self.date = date
        self.month_view.set_date(self.date)

        self.month_year_label.set_markup(self.date.strftime(MONTH_YEAR_TEMPLATE))


    def add_event(self, event):

        self.month_view.add_event(event)

    def remove_event(self, event):

        self.view.remove_event(event)

    def update_event(self, event):

        self.month_view.update_event(event)


    def set_calendars(self, calendars):

        for child in self.calendars.get_children():
            self.calendars.remove(child)
            child.destroy()

        for calendar in calendars:
            tag = Tag(calendar['uid'], calendar['name'], calendar['color'], calendar['active'])
            tag.show()
            self.calendars.pack_start(tag, False, False, 0)

            tag.connect('activity-changed', self.calendar_state_change_cb)

    def month_change_cb(self, button):

        if button == self.button_previous:
            self.set_date(self.date.previous_month)
        elif button == self.button_next:
            self.set_date(self.date.next_month)


    def calendar_state_change_cb(self, calendar, state):

        self.emit('calendar-state-changed', calendar.uid, state)
