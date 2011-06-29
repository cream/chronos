import time
import cairo
import calendar

from gi.repository import GObject as gobject, Gtk as gtk, Gdk as gdk

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

PADDING = 10
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

        self.dates = ordereddict()
        self._events = {}

        self._grid_height = 0
        self.grid_origin = (0, 0)

        self.set_size_request(500, 500)
        self.set_events(self.get_events() | gdk.EventMask.BUTTON_PRESS_MASK)

        self.connect('draw', self.draw)
        self.connect('button-press-event', self.button_press_cb)


    @property
    def events(self):
        """
        Yields events in current month
        """
        for event in self._events.itervalues():
            if self.event_in_current_month(event):
                yield event


    def add_event(self, event):

        self._events[event.uid] = event

        if self.event_in_current_month(event):
            self.queue_draw()

    def remove_event(self, event):

        self._events.pop(event.uid)

        if self.event_in_current_month(event):
            self.queue_draw()


    def update_event(self, event):

        self._events[event.uid] = event

        if self.event_in_current_month(event):
            self.queue_draw()


    def set_date(self, date):

        self.date = date
        self.queue_draw()


    def event_in_current_month(self, event):

        if event.start.month  != self.date.month:
            return False
        elif event.end.month  != self.date.month:
            return False

        if event.start.year != self.date.year:
            return False
        elif event.end.year != self.date.year:
            return False
        return True


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



    @property
    def grid_width(self):
        return self.get_allocation().width / 7


    @property
    def grid_height(self):
        weeks = number_of_weeks(self.date.year, self.date.month)
        return (self._grid_height - PADDING_BOTTOM) / weeks


    def draw(self, widget, ctx):

        width = self.get_allocation().width
        height = self.get_allocation().height

        ctx.set_operator(cairo.OPERATOR_OVER)


        # clear background
        ctx.set_source_rgb(255, 255, 255)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        used_height = self.draw_weekday_headers(ctx, 5)

        self.grid_origin = (PADDING_LEFT, used_height + PADDING)

        self._grid_height = height - self.grid_origin[1]

        self.draw_grid(ctx, self.grid_origin[1])

        self.draw_events(ctx)


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
            x = self.grid_origin[0] + column * (self.grid_width - 1)
            self.draw_line(ctx, x, y, x, height - PADDING_BOTTOM)

        year, month = self.date.year, self.date.month
        monthdates = iter_month_dates(year, month)
        for row in range(number_of_weeks(year, month)):
            y2 = y + row*self.grid_height

            # draw horizontal lines
            self.draw_line(ctx, self.grid_origin[0], y2, width - PADDING_RIGHT, y2)

            # draw the dates
            for column in range(7):
                x = self.grid_origin[0] + column * ( self.grid_width - 1)
                try:
                    d = monthdates.next()
                    if not d in self.dates:
                        self.dates[d] = Date(d, x, None, d.month != month)
                    y3 = self.draw_day(ctx, self.dates[d], x + self.grid_width, y2)
                    self.dates[d].x = x
                    self.dates[d].y = y3
                except StopIteration:
                    break

        # draw bottom line
        self.draw_line(ctx, self.grid_origin[0], y2 + self.grid_height,
                        width - PADDING_RIGHT, y2 + self.grid_height)

        # map the events to the dates
        for event in self.events:
            dates = self._get_dates_for_event(event)
            for date in dates:
                date.add_event(event)


    def draw_events(self, ctx):

        height = calculate_event_height(self.events, ctx)

        for event in self.events:

            dates = self._get_dates_for_event(event)

            if len(dates) == 1:
                self._draw_single_day_event(ctx, event, dates[0], height)
                continue

            y = calculate_y_coords(event, dates, height)

            start = dates.pop(0)
            end = dates.pop()

            # draw start and end
            ctx.set_source_rgb(*event.color)
            roundedrect(ctx, start.x, y[0], self.grid_width, height, right=False)
            roundedrect(ctx, end.x, y[-1], self.grid_width, height, left=False)
            ctx.fill()

            row = 0
            for date in dates:
                if date.first_day_of_week:
                    row += 1
                ctx.set_source_rgb(*event.color)
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

        ctx.set_source_rgb(*event.color)
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


    def draw_day(self, ctx, date, x, y):
        """
        Draw the day into the right upper corner of each box. x and y specify
        the upper right corner coordinates.
        Also draw background grey if date is outside of month
        """

        ctx.set_source_rgba(*COLOR_GREY)
        ctx.select_font_face(*FONT_NORMAL)
        ctx.set_font_size(FONT_SIZE_DAY)

        day = str(date.datetime.day)
        _, _, t_width, t_height = get_text_extents(ctx, day)
        x1 = x - t_width - PADDING_DAY
        y1 = y + t_height + PADDING_DAY
        ctx.move_to(x1, y1)
        ctx.show_text(day)

        if date.outside:
            ctx.set_source_rgba(0, 0, 0, 0.1)
            x2 = x - self.grid_width
            ctx.rectangle(x2, y, self.grid_width-1, self.grid_height)
            ctx.fill()
        if date.selected:
            ctx.set_source_rgba(0, 0, 45, 0.1)
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
