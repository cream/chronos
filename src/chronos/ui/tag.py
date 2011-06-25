from gi.repository import Gtk as gtk
import cairo
from math import pi
import colorsys

# TODO: Move to chronos.ui.util
def darken(r, g, b):

    offset = .1

    hsv = colorsys.rgb_to_hsv(r, g, b)
    c = (hsv[0], hsv[1], hsv[2] - offset)

    return colorsys.hsv_to_rgb(*c)


class Tag(gtk.DrawingArea):

    __gtype_name__ = 'Tag'

    def __init__(self, label, color):

        gtk.DrawingArea.__init__(self)
        self.connect('draw', self.draw_cb)
        self.set_property('height-request', 32)
        
        self.label = label
        self.color = color
        
        
    def draw_cb(self, drawing_area, ctx):
    
        ctx.select_font_face("Droid Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(12)
    
        t_xbearing, t_ybearing, t_width, t_height, t_xadvance, t_yadvance = ctx.text_extents(self.label)
    
        width = t_width + 45
        height = self.get_preferred_height()[0]
        
        self.set_size_request(width, height)
        
        ctx.save()
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_line_width(1)
        ctx.translate(.5, .5)
        
        ctx.move_to(5, 6)
        ctx.line_to(width-18, 6)
        ctx.line_to(width-10, 6 + (height-12)*1.0/3.0)
        ctx.line_to(width-10, 6 + (height-12)*2.0/3.0)
        ctx.line_to(width-18, height-6)
        ctx.line_to(5, height-6)
        ctx.line_to(5, 6)
        
        ctx.new_sub_path()
        ctx.arc(width - 16, height/2.0, 3, 0, 2*pi)
        
        ctx.set_source_rgb(*self.color)
        ctx.fill_preserve()
        
        ctx.set_source_rgb(*darken(*self.color))
        ctx.stroke()
        ctx.restore()
        
        ctx.save()
        ctx.set_source_rgb(.3, 0, 0)
        ctx.move_to(width - 16, height/2.0)
        ctx.rel_curve_to(3, 0, 6, 5, 8, 0)
        ctx.move_to(width - 9, height/2.0+2)
        ctx.rel_curve_to(1, 5, 3, 5, 2, 7)
        ctx.stroke()
        ctx.restore()
        
        ctx.move_to(16-t_xbearing, (self.get_preferred_height()[0] - t_ybearing) / 2.0)
        ctx.show_text(self.label)
        ctx.stroke()

