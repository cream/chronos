from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GdkPixbuf as pixbuf
import cairo


class CalendarView(gtk.VBox):

    def __init__(self, interface):
    
        gtk.VBox.__init__(self)
        
        self.calendar_view = interface.get_object('calendar_view')
        self.add(self.calendar_view)
        
        self.calendar_store = interface.get_object('calendar_store')
        self.calendar_active = interface.get_object('calendar_active')
        self.calendar_active.connect('toggled', self.on_toggle)
        
        
    def add_calendar(self, calendar):
    
        self.calendar_store.append( (calendar['name'], calendar['uid'], True,) )
        
        
    def on_toggle(self, widget, path):
    
        active = self.calendar_store[path][2]
        self.calendar_store[path][2] = not active

