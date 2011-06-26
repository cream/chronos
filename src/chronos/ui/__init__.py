import os
import colorsys
from gi.repository import Gtk as gtk

from chronos.ui.month import MonthView
from chronos.ui.day import DayView
from chronos.ui.tag import Tag

# TODO: Move to chronos.ui.util
def find_colors(r, g, b):

    offset = 1.0/6
    
    hsv = colorsys.rgb_to_hsv(r, g, b)
    
    while True:
        c = (hsv[0] - offset, hsv[1], hsv[2])
        offset += 1.0/6
        yield colorsys.hsv_to_rgb(*c)


class CalendarUI(object):

    def __init__(self):

        self.events = {}
        
        interface_path = os.path.join(os.path.dirname(__file__), 'calendar.ui')
        
        # Load the interface data
        self.interface = gtk.Builder()
        self.interface.add_from_file(interface_path)
        
        # Retrieve the objects being used here
        self.window = self.interface.get_object('main_window')
        self.layout = self.interface.get_object('layout')
        self.paned = self.interface.get_object('paned')
        self.button_previous = self.interface.get_object('button_previous')
        self.button_next = self.interface.get_object('button_next')

        # Construct the custom interfaces
        self.month_view = MonthView()
        self.day_view = DayView()
        
        # Connect the signals
        self.button_previous.connect('clicked', lambda *args: self.month_view.previous_month())
        self.button_next.connect('clicked', lambda *args: self.month_view.next_month())
        
        # TODO: Make use of MonthViews signals!

        self.paned.add1(self.month_view)
        self.paned.add2(self.day_view)

        # Display the calendars as tags
        self.colors = find_colors(.57, .72, .79)

        self.calendars = gtk.HBox()
        self.calendars.set_spacing(1)
        self.layout.pack_start(self.calendars, False, False, 0)

        # Show the window
        self.window.show_all()


    # TODO: This does not work!
    def add_event(self, event):

        self.events[event.uid] = event
        self.month_view.add_event(event)

    def remove_event(self, event):

        self.events.pop(event.uid)
        self.view.remove_event(event)  

    def update_event(self, event):

        self.events[event.uid] = event
        self.view.update_event(event)

    def add_calendar(self, calendar):

        color = self.colors.next()
        tag = Tag(calendar['name'], color)
        tag.show()
        self.calendars.pack_start(tag, False, False, 0)

        return color

