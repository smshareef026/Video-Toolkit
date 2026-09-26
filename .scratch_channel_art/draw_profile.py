import cairo
import math

W = H = 800
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surface)

def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

# --- background radial gradient ---
cx, cy = W * 0.38, H * 0.32
grad = cairo.RadialGradient(cx, cy, 0, cx, cy, W * 0.9)
grad.add_color_stop_rgb(0.0, *hex_rgb('b026d6'))
grad.add_color_stop_rgb(0.5, *hex_rgb('701f9e'))
grad.add_color_stop_rgb(1.0, *hex_rgb('170a26'))
ctx.set_source(grad)
ctx.rectangle(0, 0, W, H)
ctx.fill()

# --- jagged "play button with a buzz-cut edge" icon ---
points = [
    (285, 195),
    (285, 605),
    (485, 495),
    (420, 450),
    (605, 400),
    (420, 350),
    (485, 305),
]

def path(ctx):
    ctx.move_to(*points[0])
    for p in points[1:]:
        ctx.line_to(*p)
    ctx.close_path()

# gold linear gradient fill (top-left to bottom-right of icon bbox)
icon_grad = cairo.LinearGradient(240, 195, 560, 605)
icon_grad.add_color_stop_rgb(0.0, *hex_rgb('ffe27a'))
icon_grad.add_color_stop_rgb(1.0, *hex_rgb('ff9d00'))

path(ctx)
ctx.set_source(icon_grad)
ctx.fill_preserve()

ctx.set_source_rgb(*hex_rgb('2b0e40'))
ctx.set_line_width(8)
ctx.set_line_join(cairo.LINE_JOIN_ROUND)
ctx.stroke()

surface.write_to_png("profile.png")
print("wrote profile.png")
