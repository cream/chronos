import time
import cairo
import calendar
from collections import defaultdict

from gi.repository import GObject as gobject, Gtk as gtk, Gdk as gdk

from cream.util.dicts import ordereddict

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


class Date(object):

    def __init__(self, dtime, x, y, outside):

        self.datetime = dtime
        self.x = x
        self.y = y
        self.outside = outside
        self.selected = False
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

    __gtype_name__ = 'MonthView'
    __gsignals__ = {
        'month-changed': (gobject.SignalFlags.RUN_LAST, None, ()),
        'day-changed': (gobject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self, date):

        gtk.DrawingArea.__init__(self)

        self.date = date

        self.date_coords = {}
        self._events = {}

        self.set_size_request(800, 600)
        self.set_events(self.get_events() | gdk.EventMask.BUTTON_PRESS_MASK)

        self.connect('draw', self.draw)
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
                yield date, event, event_pos[row]


    def add_event(self, event):

        self._events[event.uid] = event

        self.queue_draw()

    def remove_event(self, event):

        self._events.pop(event.uid)

        self.queue_draw()


    def update_event(self, event):

        self._events[event.uid] = event

        self.queue_draw()


    def set_date(self, date):

        self.date = date
        self.queue_draw()


    def button_press_cb(self, widget, event):

        obj = self.get_object_at_coords(event.x, event.y)

        if isinstance(obj, Date):
            self.selected_date = obj.datetime

        self.queue_draw()


    def get_object_at_coords(self, x, y):

        x0 = self.grid_origin[0]
        y0 = self.grid_origin[1]
        if x < x0 or y < y0:
            return None

        ret = None
        for date in self.dates.itervalues():
            if (x > date.x and x < date.x + self.grid_width
                and y > date.y and y < date.y + self.grid_height):
                date.selected = True
                ret = date
            else:
                date.selected = False

        return ret


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

        # Draw grid
        def draw_line(ctx, x1, y1, x2, y2):
            ctx.set_source_rgba(.8, .8, .8, 1)
            ctx.set_line_width(1)
            ctx.move_to(x1 + .5, y1 + .5)
            ctx.line_to(x2 + .5, y2 + .5)
            ctx.stroke()

        y += PADDING

        grid_height = height - y - PADDING_BOTTOM
        num_weeks = number_of_weeks(self.date.year, self.date.month)
        cell_height = grid_height / float(num_weeks)

        x = x2 = PADDING_LEFT

        # Draw rightmost line
        draw_line(ctx, int(x2), int(y), int(x2), int(y + grid_height))

        # Draw horizontal lines and dates
        monthdates = iter_month_dates(self.date.year, self.date.month)
        y2 = y
        draw_line(ctx, x, y2, width - PADDING_RIGHT, y2)
        for i, date in enumerate(monthdates):
            if date.weekday() == 0 and i != 0:
                # New row, new line
                y2 += cell_height
                draw_line(ctx, int(x), int(y2), int(width-PADDING_RIGHT), int(y2))

            # Draw the day into the right upper corner
            ctx.set_source_rgba(*COLOR_GREY)
            ctx.select_font_face(*FONT_NORMAL)
            ctx.set_font_size(FONT_SIZE_DAY)

            x2 = x + cell_width * (date.weekday() + 1)

            day = str(date.day)
            _, _, t_width, t_height = get_text_extents(ctx, day)
            x3 = x2 - t_width - PADDING_DAY
            y3 = y2 + t_height + PADDING_DAY
            ctx.move_to(int(x3), int(y3))
            ctx.show_text(day)
            self.date_coords[date.as_date] = (int(x2) - int(cell_width), int(y3) + PADDING_DAY)

            if date.month != self.date.month:
                # Draw the day grey, it sucks!
                ctx.set_source_rgba(0, 0, 0, 0.05)
                x2 = x + cell_width * (date.weekday())
                ctx.rectangle(int(x2)+1, int(y2)+1, int(cell_width), int(cell_height)-1)
                ctx.fill()

        # Draw bottom line
        y2 = height - PADDING_BOTTOM
        draw_line(ctx, x, y2, width - PADDING_RIGHT, y2)

        # Draw events
        event_height = calculate_event_height(self.events, ctx)

        for date, event, row in self.events:
            x2, y2 = self.date_coords[date.as_date]
            y2 += row * (event_height + PADDING_DAY)
            ctx.set_source_rgb(*event.color)

            if (event.start.as_date == date.as_date and
                event.end.as_date == date.as_date):
                roundedrect(ctx, int(x2+5), int(y2), int(cell_width-10), int(event_height), 8)
            elif event.start.as_date == date.as_date:
                roundedrect(ctx, int(x2+5), int(y2), int(cell_width-5), int(event_height), 8, right=False)
            elif event.end.as_date == date.as_date:
                roundedrect(ctx, int(x2), int(y2), int(cell_width-5), int(event_height), 8, left=False)
            else:
                ctx.rectangle(int(x2), int(y2), int(cell_width), int(event_height))

            ctx.fill()

        # Draw vertical lines
        x2 = x
        for column in range(8):
            draw_line(ctx, int(x2), int(y), int(x2), int(y + grid_height))
            x2 += cell_width

        for date, event, row in self.events:
            x2, y2 = self.date_coords[date.as_date]
            y2 += row * (event_height + PADDING_DAY)
            if date == event.start or date.first_day_of_week:
                ctx.save()
                ctx.set_source_rgb(0, 0, 0)
                ctx.move_to(x2 + PADDING_TITLE_LEFT, y2 + 11)
                ctx.show_text(event.title)
                ctx.restore()


def get_text_extents(ctx, text):
    return ctx.text_extents(text)[:4]


def calculate_event_height(events, ctx):
    """
    Calculates the maximum height for all events
    """

    height = 0
    for date, event, row in events:
        height = max(height, get_text_extents(ctx, event.title)[3])

    return height + 2*PADDING_TITLE


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
