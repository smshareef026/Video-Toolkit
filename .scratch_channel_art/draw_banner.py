import cairo
import math
import random

W, H = 2560, 1440

def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surface)

# --- background gradient ---
cx, cy = W * 0.5, H * 0.42
grad = cairo.RadialGradient(cx, cy, 0, cx, cy, W * 0.75)
grad.add_color_stop_rgb(0.0, *hex_rgb('9a1fc9'))
grad.add_color_stop_rgb(0.55, *hex_rgb('641b8c'))
grad.add_color_stop_rgb(1.0, *hex_rgb('120820'))
ctx.set_source(grad)
ctx.rectangle(0, 0, W, H)
ctx.fill()

# --- subtle diagonal speed-line texture (kept low opacity, behind text) ---
random.seed(7)
ctx.save()
ctx.set_line_width(3)
for i in range(26):
    y = random.uniform(-100, H + 100)
    length = random.uniform(220, 620)
    x = random.uniform(-200, W + 200)
    alpha = random.uniform(0.03, 0.07)
    ctx.set_source_rgba(1, 1, 1, alpha)
    ctx.move_to(x, y)
    ctx.line_to(x - length * 0.45, y + length)
    ctx.stroke()
ctx.restore()

# --- icon: jagged play/buzz-cut shape, scaled + translated into the left of the safe zone ---
base_points = [
    (285, 195), (285, 605), (485, 495), (420, 450),
    (605, 400), (420, 350), (485, 305),
]
icon_scale = 0.62
icon_offset_x = 560
icon_offset_y = 720  # banner vertical center -- keeps icon inside the ~508-931 safe zone

# base bbox center is (400,400) in original 800x800 space
def transform(p):
    x, y = p
    return (
        icon_offset_x + (x - 400) * icon_scale,
        icon_offset_y + (y - 400) * icon_scale,
    )

pts = [transform(p) for p in base_points]

icon_grad = cairo.LinearGradient(pts[0][0], pts[0][1], pts[4][0], pts[4][1])
icon_grad.add_color_stop_rgb(0.0, *hex_rgb('ffe27a'))
icon_grad.add_color_stop_rgb(1.0, *hex_rgb('ff9d00'))

ctx.move_to(*pts[0])
for p in pts[1:]:
    ctx.line_to(*p)
ctx.close_path()
ctx.set_source(icon_grad)
ctx.fill_preserve()
ctx.set_source_rgb(*hex_rgb('2b0e40'))
ctx.set_line_width(6)
ctx.set_line_join(cairo.LINE_JOIN_ROUND)
ctx.stroke()

# --- wordmark ---
ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
title = "THE BUZZ CUT"
title_size = 128
ctx.set_font_size(title_size)
text_x = 920
# vertical baseline centered so the title+tagline block sits in the ~508-931 safe zone
title_baseline_y = 760

# soft shadow for legibility
ctx.set_source_rgba(0, 0, 0, 0.35)
ctx.move_to(text_x + 6, title_baseline_y + 6)
ctx.show_text(title)

ctx.set_source_rgb(*hex_rgb('fdf6ea'))
ctx.move_to(text_x, title_baseline_y)
ctx.show_text(title)

# --- tagline ---
ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
tagline = "E N T E R T A I N M E N T .   U N C U T ."
ctx.set_font_size(40)
ctx.set_source_rgb(*hex_rgb('ffd27a'))
ctx.move_to(text_x + 6, title_baseline_y + 74)
ctx.show_text(tagline)

surface.write_to_png("banner.png")
print("wrote banner.png")

# --- debug copy with safe-zone guide overlay ---
sx, sy = (W - 1546) / 2, (H - 423) / 2
ctx.set_source_rgba(0, 1, 1, 0.9)
ctx.set_line_width(3)
ctx.set_dash([14, 10])
ctx.rectangle(sx, sy, 1546, 423)
ctx.stroke()
surface.write_to_png("banner_debug.png")
print("wrote banner_debug.png")
