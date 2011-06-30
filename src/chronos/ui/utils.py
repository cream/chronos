import colorsys


def find_colors(r, g, b):

    offset = 1.0/6

    hsv = colorsys.rgb_to_hsv(r, g, b)

    while True:
        c = (hsv[0] - offset, hsv[1], hsv[2])
        offset += 1.0/6
        yield colorsys.hsv_to_rgb(*c)
