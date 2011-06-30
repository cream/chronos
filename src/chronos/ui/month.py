import time
import cairo
import calendar
from collections import defaultdict

from gi.repository import GObject as gobject, Gtk as gtk, Gdk as gdk

from chronos.utils import datetime, iter_month_dates, number_of_weeks, \
                          iter_date_range, first_day_of_week, \
                          last_day_of_week


MONTH_YEAR_TEMPLATE = '%B %Y' # e.g. June 2011

FONT_NORMAL = ('Droid Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
FONT_BOLD = ('Droid Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
FONT_SIZE_MONTH_YEAR = 20
FONT_SIZE_WEEKDAY = 11
FONT_SIZE_DAY = 11
FONT_SIZE_EVENT = 10
COLOR = (.1, .1, .1, 1)
COLOR_GREY = (.1, .1, .1, 0.5)

PADDING = 10
PADDING_TOP = 5
PADDING_BOTTOM = 5
PADDING_LEFT = 5
PADDING_RIGHT = 5
PADDING_DAY = 5
PADDING_TITLE = 3
PADDING_TITLE_LEFT = 8
PADDING_EVENT = 3


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


class MonthView(gtk.DrawingArea):

    __gtype_name__ = 'MonthView'
    __gsignals__ = {
        'month-changed': (gobject.SignalFlags.RUN_LAST, None, ()),
        'day-changed': (gobject.SignalFlags.RUN_LAST, None, ()),
        'day-selected': (gobject.SignalFlags.RUN_LAST, None, (object,)),
    }

    def __init__(self, date):

        gtk.DrawingArea.__init__(self)

        self.date = date

        self.cells = []
        for column in range(7):
            self.cells.append([])
            for row in range(7):
                self.cells[column].append({})
        self._events = {}
        self.grid_origin = (0, 0)

        self.set_size_request(800, 600)
        self.set_events(self.get_events() | gdk.EventMask.BUTTON_PRESS_MASK)

        self.connect('draw', self.draw)
        self.connect('size-allocate', lambda *x: self.calculate_cell_data())
        self.connect('button-press-event', self.button_press_cb)


    @property
    def events(self):
        """
        Yields events in current month
        """

        def event_larger_in_week(date, e1, e2):
            weekstart = first_day_of_week(date)
            weekend = last_day_of_week(date)

            if e1.start < weekstart:
                e1_start = weekstart
            else:
                e1_start = e1.start

            if e1.end > weekend:
                e1_end = weekend
            else:
                e1_end = e1.end

            if e2.start < weekstart:
                e2_start = weekstart
            else:
                e2_start = e2.start

            if e2.end > weekend:
                e2_end = weekend
            else:
                e2_end = e2.end

            if e1_end - e1_start > e2_end - e2_start:
                return True
            return False

        def get_date_range(event):
            for date in iter_date_range(event.start, event.end):
               if date.year == self.date.year and date.month == self.date.month:
                    yield date

        events = filter(lambda e: e.active, self._events.itervalues())

        # map events to dates
        events_by_date = defaultdict(list)
        for event in events:
            for date in get_date_range(event):
                events_by_date[date.as_date].append(event)

        dates = defaultdict(list)
        # calculate the position of a event for every row
        for event in events:
            event_pos = [0]
            for date in get_date_range(event):
                if date.first_day_of_week:
                    event_pos.append(0)
                for other_event in events_by_date[date.as_date]:
                    if other_event == event:
                        continue
                    if not event_larger_in_week(date, event, other_event):
                        event_pos[-1] += 1
            row = 0
            for i, date in enumerate(get_date_range(event)):
                if date.first_day_of_week and i != 0:
                    row += 1
                dates[date].append((event, event_pos[row]))

        return dates


    def add_events(self, events):

        for event in events:
            self._events[event.uid] = event

        self.update_cell_events()
        self.queue_draw()

    def remove_events(self, events):

        for event in events:
            self._events.pop(event.uid)

        self.update_cell_events()
        self.queue_draw()


    def update_events(self, events):

        for event in events:
            self._events[event.uid] = event

        self.update_cell_events()
        self.queue_draw()


    def set_date(self, date):

        self.date = date
        self.calculate_cell_data()
        self.queue_draw()


    def update_cell_events(self):

        events_by_date = self.events
        for row in self.cells:
            for cell in row:
                if 'date' in cell:
                    cell['events'] = events_by_date[cell['date']]


    def calculate_cell_data(self):

        width = self.get_allocation().width
        height = self.get_allocation().height

        x, y = self.grid_origin

        grid_height = height - y - PADDING_BOTTOM
        num_weeks = number_of_weeks(self.date.year, self.date.month)
        cell_height = grid_height / float(num_weeks)
        cell_width = (width - PADDING_LEFT - PADDING_RIGHT) / 7.0

        monthdates = iter_month_dates(self.date.year, self.date.month)

        y2 = y
        for row in range(num_weeks):
            x2 = x
            for column in range(7):
                d = self.cells[column][row]
                d['x'] = x2
                d['y'] = int(y2)
                d['width'] = int(cell_width)
                d['height'] = int(cell_height)
                d['date'] = monthdates.next()
                if not 'selected' in d:
                    d['selected'] = False
                x2 += cell_width
            y2 += cell_height

        self.update_cell_events()


    def button_press_cb(self, widget, event):

        x, y = event.x, event.y

        num_weeks = number_of_weeks(self.date.year, self.date.month)
        for column in range(7):
            for row in range(num_weeks):
                c_x = self.cells[column][row]['x']
                c_y = self.cells[column][row]['y']
                c_w = self.cells[column][row]['width']
                c_h = self.cells[column][row]['height']

                if (in_rect(x, y, c_x, c_y, c_w, c_h)):
                    self.cells[column][row]['selected'] = True
                    self.emit('day-selected', self.cells[column][row]['date'])
                    should_redraw = True
                else:
                    self.cells[column][row]['selected'] = False

        if should_redraw:
            self.queue_draw()


    def draw(self, widget, ctx):

        width = self.get_allocation().width
        height = self.get_allocation().height

        ctx.set_operator(cairo.OPERATOR_OVER)

        # clear background
        ctx.set_source_rgb(255, 255, 255)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        cell_width = (width - PADDING_LEFT - PADDING_RIGHT) / 7.0

        # Draw weekdays
        ctx.set_source_rgba(*COLOR_GREY)
        ctx.select_font_face(*FONT_NORMAL)
        ctx.set_font_size(FONT_SIZE_WEEKDAY)

        y = PADDING_TOP

        for i, weekday in enumerate(calendar.Calendar().iterweekdays()):
            dayname = calendar.day_name[weekday]

            _, _, t_width, t_height = get_text_extents(ctx, dayname)
            x = i * cell_width + cell_width/2 - t_width/2
            y = max(y, t_height + PADDING_TOP)

            ctx.move_to(x, y)
            ctx.show_text(dayname)

        if self.grid_origin != (PADDING_LEFT, y + PADDING):
            self.grid_origin = (PADDING_LEFT, y + PADDING)
            self.calculate_cell_data()
        self.grid_origin = (PADDING_LEFT, y + PADDING)

        # calculate the maximal event height
        event_height = 0
        for events in self.events.values():
            event_height = max(calculate_event_height(events[0][0], ctx), event_height)

        num_weeks = number_of_weeks(self.date.year, self.date.month)
        for column in range(7):
            for row in range(num_weeks):
                x = self.cells[column][row]['x']
                y = self.cells[column][row]['y']
                cell_width = self.cells[column][row]['width']
                cell_height = self.cells[column][row]['height']
                date = self.cells[column][row]['date']
                events = self.cells[column][row]['events']
                selected = self.cells[column][row]['selected']

                if date.month != self.date.month:
                    # Draw the day grey, it sucks!
                    ctx.set_source_rgba(0, 0, 0, 0.05)
                    ctx.rectangle(x, y, cell_width, cell_height)
                    ctx.fill()

                if selected:
                    ctx.set_source_rgba(0, 0, 0.1, 0.1)
                    ctx.rectangle(x+1, y+1, cell_width, cell_height)
                    ctx.fill()

                # Draw the day into the right upper corner
                ctx.set_source_rgba(*COLOR_GREY)
                ctx.select_font_face(*FONT_NORMAL)
                ctx.set_font_size(FONT_SIZE_DAY)

                _, _, t_width, t_height = get_text_extents(ctx, str(date.day))
                x2 = x + cell_width - t_width - PADDING_DAY
                y2 = y + t_height + PADDING_DAY
                ctx.move_to(x2, y2)
                ctx.show_text(str(date.day))

                # Draw events
                for event, i in events:
                    ctx.set_source_rgb(*event.color)

                    y3 = int(y2 + PADDING_EVENT + i * (event_height + PADDING_EVENT))

                    if (event.start.as_date == date.as_date and
                        event.end.as_date == date.as_date):
                        roundedrect(ctx, x+5, y3, cell_width-10, event_height, 8)
                    elif event.start.as_date == date.as_date:
                        roundedrect(ctx, x+5, y3, cell_width-4, event_height, 8, right=False)
                    elif event.end.as_date == date.as_date:
                        roundedrect(ctx, x, y3, cell_width-5, event_height, 8, left=False)
                    else:
                        ctx.rectangle(x, y3, cell_width+1, event_height)

                    ctx.fill()

        # Draw grid
        def draw_line(ctx, x1, y1, x2, y2):
            ctx.set_source_rgba(.8, .8, .8, 1)
            ctx.set_line_width(1)
            ctx.move_to(int(x1) + .5, int(y1) + .5)
            ctx.line_to(int(x2) + .5, int(y2) + .5)
            ctx.stroke()

        for column in range(7):
            for row in range(num_weeks):
                x = self.cells[column][row]['x']
                y = self.cells[column][row]['y']

                # Draw horizontal line
                if column == 0:
                    draw_line(ctx, x, y, width - PADDING_RIGHT, y)
                # Draw vertical line
                if row == 0:
                    draw_line(ctx, x, y, x, height - PADDING_BOTTOM)
                # Draw rightmost line
                if row == 0 and column == 6:
                    x2 = int(x + cell_width)
                    draw_line(ctx, x2, y, x2, height - PADDING_BOTTOM)


            # Draw bottom line
            if column == 0:
                y = int(y + cell_height)
                draw_line(ctx, x, y, width - PADDING_RIGHT, y)

        for column in range(7):
            for row in range(num_weeks):
                x = self.cells[column][row]['x']
                y = self.cells[column][row]['y']
                date = self.cells[column][row]['date']
                events = self.cells[column][row]['events']

                ctx.select_font_face(*FONT_NORMAL)
                ctx.set_font_size(FONT_SIZE_DAY)

                _, _,_, t_height = get_text_extents(ctx, str(date.day))

                y2 = y + t_height + PADDING_DAY

                # Draw event titles
                ctx.set_source_rgb(0, 0, 0)
                for event, i in events:
                    y3 = int(y2 + PADDING_EVENT + i * (event_height + PADDING_EVENT))
                    if date == event.start.as_date or date.first_day_of_week:
                        ctx.move_to(x + PADDING_TITLE_LEFT, y3 + 11)
                        ctx.show_text(event.title)



def get_text_extents(ctx, text):
    return ctx.text_extents(text)[:4]


def calculate_event_height(event, ctx):
    """
    Calculates the height for the event
    """

    return int(get_text_extents(ctx, event.title)[3] + 2*PADDING_TITLE)


def calculate_y_coords(event, dates, height):
    """
    Calculates the y position of the event for each row.
    """

    y = [0]
    for date in dates:
        if date.first_day_of_week and date != dates[0]:
            y.append(0)
        position = date.position_of_event(event)
        y[-1] = max(y[-1], date.y + position*height + PADDING_EVENT*position)

    return y

def in_rect(x, y, x0, y0, w, h):
    """
    Returns if x and y are in the rectangle specified by x0, y0, w, h
    """
    return x > x0 and x < x0 + w and y > y0 and y < y0 + h
