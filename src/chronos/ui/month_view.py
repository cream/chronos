import time
import cairo
import calendar

from gi.repository import Gtk as gtk

from cream.util.dicts import ordereddict

from chronos.utils import datetime, iter_month_dates, number_of_weeks


MONTH_YEAR_TEMPLATE = '%B %Y' # e.g. June 2011

FONT_NORMAL = ('Droid Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
FONT_BOLD = ('Droid Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
FONT_SIZE_MONTH_YEAR = 20
FONT_SIZE_WEEKDAY = 11
FONT_SIZE_DAY = 11
FONT_SIZE_EVENT = 10
COLOR = (.1, .1, .1, 1)
COLOR_GREY = (.1, .1, .1, 0.5)

PADDING = 15
PADDING_TOP = 5
PADDING_BOTTOM = 5
PADDING_LEFT = 5
PADDING_RIGHT = 5
PADDING_DAY = 5
PADDING_TITLE = 1
PADDING_TITLE_LEFT = 5
PADDING_EVENT = 2


def roundedrect(ctx, x, y, w, h, r = 15, left=True, right=True):
    "Draw a rounded rectangle"
    #   A****BQ
    #  H      C
    #  *      *
    #  G      D
    #  PF****E

    ctx.move_to(x+r,y)                      # Move to A
    if right:
        ctx.line_to(x+w-r,y)                # Straight line to B
        ctx.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
        ctx.line_to(x+w,y+h-r)                  # Move to D
        ctx.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
    else:
        ctx.line_to(x+w,y)                    # Straight line to Q
        ctx.line_to(x+w, y+h)                 # Straight line to E
    
    if left:
        ctx.line_to(x+r,y+h)                    # Line to F
        ctx.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
        ctx.line_to(x,y+r)                      # Line to H
        ctx.curve_to(x,y,x,y,x+r,y)             # Curve to A
    else:
        ctx.line_to(x,y+h)                    # Straight line to P
        ctx.line_to(x, y)                     # Straight line to A


class Date(object):

    def __init__(self, dtime, x, y):
    
        self.datetime = dtime
        self.x = x
        self.y = y
        self.first_day_of_week = self.datetime.weekday() == 0
        self.last_day_of_week = self.datetime.weekday() == 6
        
        self.events = ordereddict()
        
    
    def add_event(self, event):
    
        self.events[event.uid] = event
    
        # sort events after length
        new = ordereddict()
        events = sorted(self.events.values(), key=lambda d: d.end - d.start, reverse=True)
        for event in events:
            new[event.uid] = event
        
        self.events = new
        

    def position_of_event(self, event):
        
        return self.events.values().index(event) 


class MonthView(gtk.DrawingArea):

    def __init__(self, interface):
    
        self.selected_date = datetime.now()
        self.dates = ordereddict()
        self._events = {}
        
        self._grid_height = 0
        
        self.next = interface.get_object('next')
        self.previous = interface.get_object('previous')
        self.next.connect('clicked', self.month_change_cb)
        self.previous.connect('clicked', self.month_change_cb)
    
        gtk.DrawingArea.__init__(self)
        
        self.set_size_request(500, 500)
        
        self.connect('draw', self.draw)
        
    @property
    def events(self):
        return self._events.itervalues()
    
    def add_event(self, event):

        self._events[event.uid] = event

        if (event.start.month == self.selected_date.month
            or event.end.month == self.selected_date.month):
            self.queue_draw()

    def remove_event(self, event):

        self._events.pop(event.uid)

        if (event.start.month == self.selected_date.month
            or event.end.month == self.selected_date.month):
            self.queue_draw()


    def update_event(self, event):

        self._events[event.uid] = event

        if (event.start.month == self.selected_date.month
            or event.end.month == self.selected_date.month):
            self.queue_draw()


    def month_change_cb(self, button):

        if button == self.previous:
            self.selected_date = self.selected_date.previous_month()
            self.queue_draw()
        elif button == self.next:
            self.selected_date = self.selected_date.next_month()
            self.queue_draw()
        
    
    @property
    def grid_width(self):
        return self.get_allocation().width / 7
        
    
    @property
    def grid_height(self):
        weeks = number_of_weeks(self.selected_date.year, self.selected_date.month)
        return (self._grid_height - PADDING_BOTTOM) / weeks
                
    
    def do_get_preferred_width_for_height(self, height):
        
        return height, height

        
    def do_get_preferred_height_for_width(self, width):

        return 0.8*width, 0.8*width
        

    def draw(self, widget, ctx):
    
        self.dates = ordereddict()
    
        width = self.get_allocation().width
        height = self.get_allocation().height
        
        ctx.set_operator(cairo.OPERATOR_OVER)

        
        # clear background
        ctx.set_source_rgb(255, 255, 255)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()
        
        used_height = self.draw_date_label(ctx, 0)
        
        used_height += self.draw_weekday_headers(ctx, used_height + PADDING)
        
        self._grid_height = height - (used_height - PADDING)
        
        self.draw_grid(ctx, used_height - PADDING)
        
        self.draw_events(ctx)
        
    
    def draw_date_label(self, ctx, start_height):
    
        width = self.get_allocation().width
        height = self.get_allocation().height
        
        ctx.set_source_rgba(*COLOR)
        ctx.select_font_face(*FONT_BOLD)
        ctx.set_font_size(FONT_SIZE_MONTH_YEAR)
        
        text = self.selected_date.strftime(MONTH_YEAR_TEMPLATE)
        _, _, t_width, t_height = get_text_extents(ctx, text)
        
        ctx.move_to(width/2 - t_width/2, PADDING_TOP + t_height)
        ctx.show_text(text)
        
        return PADDING_TOP + t_height
        
    
    def draw_weekday_headers(self, ctx, start_height):

        y = start_height

        ctx.set_source_rgba(*COLOR_GREY)
        ctx.select_font_face(*FONT_NORMAL)
        ctx.set_font_size(FONT_SIZE_WEEKDAY)
    
        for i, weekday in enumerate(calendar.Calendar().iterweekdays()):
            dayname = calendar.day_name[weekday]
            
            _, _, t_width, t_height = get_text_extents(ctx, dayname)
            x = i * self.grid_width
            y = max(y, start_height + t_height )
            
            ctx.move_to(x + self.grid_width/2 - t_width/2, y)
            ctx.show_text(dayname)
            
        
        return y
        
    
    def draw_grid(self, ctx, start_height):
    
        y = start_height
        width = self.get_allocation().width
        height = self.get_allocation().height
        
        # draw vertical lines
        for column in range(8):
            x = PADDING_LEFT + column * (self.grid_width - 1)
            self.draw_line(ctx, x, y, x, height - PADDING_BOTTOM)
        
        year, month = self.selected_date.year, self.selected_date.month
        monthdates = iter_month_dates(year, month)
        for row in range(number_of_weeks(year, month)):
            y2 = y + row*self.grid_height
            
            # draw horizontal lines
            self.draw_line(ctx, PADDING_LEFT, y2, width - PADDING_RIGHT, y2)
            
            for column in range(7):
                x = PADDING_LEFT + column * ( self.grid_width - 1)
                try:
                    d = monthdates.next()
                    y3 = self.draw_day(ctx, d.day, x + self.grid_width, y2, d.month != month)
                    self.dates[d] = Date(d, x, y3)
                except StopIteration:
                    break
        
        # draw bottom line
        self.draw_line(ctx, PADDING_LEFT, y2 + self.grid_height, 
                        width - PADDING_RIGHT, y2 + self.grid_height)
        
        # map the events to the dates
        for event in self.events:
            dates = self._get_dates_for_event(event)
            for date in dates:
                date.add_event(event)
    
    
    def draw_events(self, ctx):
    
        height = calculate_event_height(self.events, ctx)
    
        for event in self.events:
            if (event.start.month != self.selected_date.month 
                and event.end.month != self.selected_date.month):
                continue
        
            dates = self._get_dates_for_event(event)
            
            if len(dates) == 1:
                self._draw_single_day_event(ctx, event, dates[0], height)
                continue
            
            y = calculate_y_coords(event, dates, height)

            start = dates.pop(0)
            end = dates.pop()

            # draw start and end
            ctx.set_source_rgba(0, 45, 0, 0.5)
            roundedrect(ctx, start.x, y[0], self.grid_width, height, right=False)
            roundedrect(ctx, end.x, y[-1], self.grid_width, height, left=False)
            ctx.fill()
            
            row = 0
            for date in dates:
                if date.first_day_of_week:
                    row += 1
                ctx.set_source_rgba(0, 45, 0, 0.5)
                if date.first_day_of_week:
                    roundedrect(ctx, date.x, y[row], self.grid_width, height, right=False)
                elif date.last_day_of_week:
                    roundedrect(ctx, date.x, y[row], self.grid_width, height, left=False)
                else:
                    ctx.rectangle(date.x, y[row], self.grid_width, height)
                ctx.fill()
                
                # calculate remaining space in row and draw event title
                if date.first_day_of_week:
                    columns  = (end.datetime - date.datetime).days + 1
                    if columns > 6:
                        columns = 7
                    self._draw_event_title(ctx, event, date.x, y[row], 
                                           columns * self.grid_width)
            
            # draw the title in the first row
            if (end.datetime - start.datetime).days >= 6:
                columns = 7
            else:
                columns = end.datetime.weekday() + 1
            self._draw_event_title(ctx, event, start.x, y[0], 
                                   columns * self.grid_width)       
    
    
    
    def _draw_single_day_event(self, ctx, event, date, height):
        
        y = calculate_y_coords(event, [date], height)[0]
            
        ctx.set_source_rgba(0, 45, 0, 0.5)
        roundedrect(ctx, date.x, y, self.grid_width, height)
        ctx.fill()
            
        self._draw_event_title(ctx, event, date.x, y, self.grid_width)
        
            
    def _draw_event_title(self, ctx, event, x, y, remaining_space):
    
        ctx.set_source_rgba(*COLOR)
        ctx.select_font_face(*FONT_BOLD)
        ctx.set_font_size(FONT_SIZE_EVENT)
        
        title = event.title
        _, _, t_width, t_height = get_text_extents(ctx, title)
        while t_width > remaining_space - 2*PADDING_TITLE:
            title = title[:-1]
            _, _, t_width, _ = get_text_extents(ctx, title)

        x = x + PADDING_TITLE_LEFT
        y = y + t_height + PADDING_TITLE
        ctx.move_to(x, y)
        ctx.show_text(title)
        

    def draw_line(self, ctx, x1, y1, x2, y2):
        
        ctx.set_source_rgba(0,0,0,0.5)
        ctx.set_line_width(0.2)
        ctx.move_to(x1, y1)
        ctx.line_to(x2 + 0.5, y2 + 0.5)
        ctx.stroke()
        
        
    def draw_day(self, ctx, day, x, y, outside):
        """
        Draw the day into the right upper corner of each box. x and y specify
        the upper right corner coordinates.
        Also draw background grey if date is outside of month
        """
        
        ctx.set_source_rgba(*COLOR_GREY)
        ctx.select_font_face(*FONT_NORMAL)
        ctx.set_font_size(FONT_SIZE_DAY)
        
        day = str(day)
        _, _, t_width, t_height = get_text_extents(ctx, day)
        x1 = x - t_width - PADDING_DAY
        y1 = y + t_height + PADDING_DAY
        ctx.move_to(x1, y1)
        ctx.show_text(day)
        
        if outside:
            ctx.set_source_rgba(0, 0, 0, 0.1)
            x2 = x - self.grid_width
            ctx.rectangle(x2, y, self.grid_width-1, self.grid_height)
            ctx.fill()
            
        return y1 + PADDING_DAY
        

    def _get_dates_for_event(self, event):

        try:
            i = self.dates.values().index(self.dates[event.start.as_date])
            j = self.dates.values().index(self.dates[event.end.as_date])
        
            return self.dates.values()[i:j+1]
        except KeyError:
            return []
        

def get_text_extents(ctx, text):
    return ctx.text_extents(text)[:4]
    

def calculate_event_height(events, ctx):
    """
    Calculates the maximum height for all events
    """

    height = 0
    for event in events:
        height = max(height, get_text_extents(ctx, event.title)[3])
    
    return height + 2*PADDING_TITLE
        
    
def calculate_y_coords(event, dates, height):
    """
    Calculates the y position of the event for each row.
    """

    y = [0]
    i = 0
    for date in dates:
        if date.first_day_of_week and date != dates[0]:
            i += 1
            y.append(0)
        position = date.position_of_event(event)
        y[i] = max(y[i], date.y + position*height + PADDING_EVENT*position)

    return y
        
        
