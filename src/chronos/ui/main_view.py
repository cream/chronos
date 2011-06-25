from gi.repository import Gtk as gtk

from chronos.ui.month_view import MonthView


class MainView(gtk.VBox):

    def __init__(self, interface):

        gtk.VBox.__init__(self)

        self.events = []

        self.day_view_toggle = interface.get_object('day_view_toggle')
        self.week_view_toggle = interface.get_object('week_view_toggle')
        self.month_view_toggle = interface.get_object('month_view_toggle')

        self.day_view_toggle.connect('toggled', self.view_change_cb)
        self.week_view_toggle.connect('toggled', self.view_change_cb)
        self.month_view_toggle.connect('toggled', self.view_change_cb)

        self.view = MonthView(interface)
        self.add(self.view)


    def add_event(self, event):

        self.events.append(event)
        self.view.add_event(event)

    def remove_event(self, event):

        self.events.remove(event)
        self.view.remove_event(event)  

    def view_change_cb(self, toggled_button):

        print toggled_button
        
        

