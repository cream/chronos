from gi.repository import Gtk as gtk


TITLE_MARKUP = '<span size="x-large">{0}</span>'


class EventView(gtk.VBox):

    def __init__(self, interface):
    
        gtk.VBox.__init__(self)
        
        self.event_view_single_wrapper = interface.get_object('event_view_single_wrapper')
        self.event_view_single_normal = interface.get_object('event_view_single_normal')
        self.event_view_single_edit = interface.get_object('event_view_single_edit')
        self.event_view_single_wrapper.add(self.event_view_single_normal)
        self.add(self.event_view_single_wrapper)
        
        self.edit_toggle = interface.get_object('edit_toggle')
        self.edit_toggle.connect('toggled', self.edit_toggled)
        
        #self.event_title_label = interface.get_object('event_title_label')
        
        #self.event_title_entry = interface.get_object('event_title_entry')
        
        self.set_event(self.event)
        
    
    @property
    def edit_mode(self):
        return self.edit_toggle.get_active()
        
    
    def set_event(self, event):
    
        self.event = event
        
        #self.event_title_label.set_markup(TITLE_MARKUP.format(event['title']))
        #self.event_title_entry.set_text(event['title'])
        
    
    def edit_toggled(self, widget):
        
        if self.edit_mode:
            self.event_view_single_wrapper.remove(self.event_view_single_normal)
            self.event_view_single_wrapper.add(self.event_view_single_edit)
        else:
            self.event_view_single_wrapper.remove(self.event_view_single_edit)
            self.event_view_single_wrapper.add(self.event_view_single_normal)
