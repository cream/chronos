from gi.repository import Gtk as gtk


class CalendarWindow(object):

    def __init__(self, interface):
    
        self.window = interface.get_object('calendar_window')
        self.calendar_view_box = interface.get_object('calendar_view_box')
        self.main_view_box = interface.get_object('main_view_box')
        self.event_view_box = interface.get_object('event_view_box')        
        
        self.window.show_all()
