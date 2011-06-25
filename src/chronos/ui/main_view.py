from gi.repository import Gtk as gtk

from chronos.ui.month_view import MonthView


class MainView(gtk.VBox):

    def __init__(self, interface):

        gtk.VBox.__init__(self)

        self.events = {}

        self.view = MonthView(interface)
        self.add(self.view)


    def add_event(self, event):

        self.events[event.uid] = event
        self.view.add_event(event)

    def remove_event(self, event):

        self.events.pop(event.uid)
        self.view.remove_event(event)  

    def update_event(self, event):

        self.events[event.uid] = event
        self.view.update_event(event)      

