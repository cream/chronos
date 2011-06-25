import os
from gi.repository import Gtk as gtk

from chronos.ui.window import CalendarWindow
from chronos.ui.calendar_view import CalendarView
from chronos.ui.main_view import MainView
from chronos.ui.event_view import EventView

class CalendarUI(object):

    def __init__(self):
        
        path = os.path.join(os.path.dirname(__file__), 'calendar.glade')
        
        interface = gtk.Builder()
        interface.add_from_file(path)
        
        self.window = CalendarWindow(interface)
        self.calendar_view = CalendarView(interface)
        self.main_view = MainView(interface)
        self.event_view = EventView(interface)

        self.window.calendar_view_box.add(self.calendar_view)
        self.window.main_view_box.add(self.main_view)
        self.window.event_view_box.add(self.event_view)      


        self.window.window.show_all()

