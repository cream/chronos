import time
import cairo
import calendar
from operator import itemgetter
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
PADDING_START = 5
PADDING_END = 5

EVENT_HEIGHT = 15


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

        def get_date_range(event):
            for date in iter_date_range(event.start, event.end):
               if date.year == self.date.year and date.month == self.date.month:
                    yield date

        events_by_date = defaultdict(list)
        for event in self._events.itervalues():
            if not event.active: continue

            position = [0] # every value in this list is the position in each row the event spawns
            dates = []
            for i, date in enumerate(get_date_range(event)):
                if date.first_day_of_week and i != 0:
                    for d in dates:
                        events_by_date[d.as_date].append((event, position[-1]))
                    position.append(0) # new row
                    dates = []
                dates.append(date)
                other_events = filter(lambda e: e != event and event_on_date(e, date) and e.active, self._events.itervalues())
                for j, other_event in enumerate(other_events):

                    size_1, size_2 = rel_event_size_in_week(event, other_event, date)

                    if size_1 == size_2:
                        # if they are equally sized then sort after the title
                        if event.title > other_event.title:
                            position[-1] += 1
                    elif size_1 < size_2:
                        if position[-1] <= j:
                            position[-1] += 1

            for d in dates:
                events_by_date[d.as_date].append((event, position[-1]))

        return events_by_date


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
        self.update_cell_events()
        self.queue_draw()


    def update_cell_events(self):

        events = self.events
        for row in self.cells:
            for cell in row:
                if 'date' in cell:
                    cell['events'] = sorted(events[cell['date']], key=itemgetter(1))


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
                d['x'] = int(x2)
                d['y'] = int(y2)
                d['width'] = int(cell_width)
                d['height'] = int(cell_height)
                d['date'] = monthdates.next()
                if not 'selected' in d:
                    d['selected'] = False
                x2 += cell_width
            y2 += cell_height


    def button_press_cb(self, widget, event):

        x, y = event.x, event.y

        should_redraw = False
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
        else:
            self.grid_origin = (PADDING_LEFT, y + PADDING)

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
                    ctx.rectangle(x, y, cell_width+1, cell_height+1)
                    ctx.fill()

                if selected:
                    ctx.set_source_rgba(0, 0, 0.5, 0.1)
                    ctx.rectangle(x, y, cell_width+1, cell_height+1)
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
                for event, pos in events:
                    ctx.set_source_rgb(*event.color)

                    y3 = int(y2 + PADDING_EVENT + pos * (EVENT_HEIGHT + PADDING_EVENT))

                    if (event.start.as_date == date.as_date and
                        event.end.as_date == date.as_date):
                        roundedrect(ctx, x+PADDING_START, y3, cell_width-(PADDING_START+PADDING_END), EVENT_HEIGHT, 8)
                    elif event.start.as_date == date.as_date:
                        roundedrect(ctx, x+PADDING_START, y3, cell_width-(PADDING_START-1), EVENT_HEIGHT, 8, right=False)
                    elif event.end.as_date == date.as_date:
                        roundedrect(ctx, x, y3, cell_width-PADDING_END, EVENT_HEIGHT, 8, left=False)
                    else:
                        ctx.rectangle(x, y3, cell_width+1, EVENT_HEIGHT)

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


        # Draw event titles
        ctx.select_font_face(*FONT_NORMAL)
        ctx.set_font_size(FONT_SIZE_DAY)
        ctx.set_source_rgb(0, 0, 0)

        for column in range(7):
            for row in range(num_weeks):
                x = self.cells[column][row]['x']
                y = self.cells[column][row]['y']
                cell_width = self.cells[column][row]['width']
                date = self.cells[column][row]['date']
                events = self.cells[column][row]['events']

                t_height = get_text_extents(ctx, str(date.day))[3]

                y2 = y + t_height + PADDING_DAY

                for event, pos in events:
                    y3 = int(y2 + PADDING_EVENT + pos * (EVENT_HEIGHT + PADDING_EVENT))
                    if date == event.start.as_date or date.first_day_of_week:
                        space = calculate_remaining_space(event, date, cell_width)

                        title = event.title
                        t_width = get_text_extents(ctx, title)[2]
                        while t_width > space and len(title) > 1:
                            title = title[:-1]
                            t_width = get_text_extents(ctx, title)[2]

                        ctx.move_to(x + PADDING_TITLE_LEFT, y3 + 11)
                        ctx.show_text(title)


def event_on_date(event, date):

    for d in iter_date_range(event.start, event.end):
        if d == date.as_date:
            return True

    return False


def rel_event_size_in_week(event1, event2, date):
    """
    Returns the relative size of two events in the week containing date.
    """

    weekstart = first_day_of_week(date)
    weekend = last_day_of_week(date)

    if event1.start < weekstart:
        event1_start = weekstart
    else:
        event1_start = event1.start

    if event2.start < weekstart:
        event2_start = weekstart
    else:
        event2_start = event2.start

    if event1.end > weekend:
        event1_end = weekend
    else:
        event1_end = event1.end

    if event2.end > weekend:
        event2_end = weekend
    else:
        event2_end = event2.end


    if event1_start > event2_start:
        start = event1_start
    else:
        start = event2_start


    return (event1_end - start), (event2_end - start)


def get_text_extents(ctx, text):
    return ctx.text_extents(text)[:4]


def in_rect(x, y, x0, y0, w, h):
    """
    Returns if x and y are in the rectangle specified by x0, y0, w, h
    """
    return x > x0 and x < x0 + w and y > y0 and y < y0 + h

def calculate_remaining_space(event, date, width):
    """
    Returns the remaining space for the event title for the row which contains date
    """
    start = first_day_of_week(date)
    end = last_day_of_week(date)

    if event.start.as_date == end.as_date:
        return width

    if event.start.as_date > start.as_date:
        start = event.start
    else:
        width -= 2*PADDING_START
    if event.end.as_date < end:
        end = event.end
    else:
        width -= PADDING_END

    width -= PADDING_TITLE_LEFT

    remaining_space = 0
    for date in iter_date_range(start, end):
        remaining_space += width
    return remaining_space
