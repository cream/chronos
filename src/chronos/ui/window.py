from gi.repository import Gtk as gtk

from chronos.utils import datetime


MONTH_YEAR_TEMPLATE = '<span size="x-large">%B %Y</span>' # e.g. June 2011

class CalendarWindow(object):

    def __init__(self, interface):
    
        self.selected_date = datetime.now()
    
        self.window = interface.get_object('calendar_window')
        self.calendar_view_box = interface.get_object('calendar_view_box')
        self.main_view_box = interface.get_object('main_view_box')
        self.event_view_box = interface.get_object('event_view_box')
        
        self.button_add = interface.get_object('button_add')
        
        self.button_previous = interface.get_object('button_previous')
        self.button_next = interface.get_object('button_next')
        
        self.button_next.connect('clicked', self.month_change_cb)
        self.button_previous.connect('clicked', self.month_change_cb)
        
        self.month_year = interface.get_object('month_year')
        self.month_year.set_markup(self.selected_date.strftime(MONTH_YEAR_TEMPLATE))
        
        self.search_box = interface.get_object('search_box')
        
        self.window.show_all()
        
    
    
    def month_change_cb(self, button):

        if button == self.button_previous:
            self.selected_date = self.selected_date.previous_month()
        elif button == self.button_next:
            self.selected_date = self.selected_date.next_month()
            
        self.month_year.set_markup(self.selected_date.strftime(MONTH_YEAR_TEMPLATE))

