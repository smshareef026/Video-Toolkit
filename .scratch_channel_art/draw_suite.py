import cairo
import random
import sys

def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))


def bg_gradient(ctx, w, h, c0, c1, c2, cx_f=0.5, cy_f=0.4, r_f=0.75):
    cx, cy = w * cx_f, h * cy_f
    grad = cairo.RadialGradient(cx, cy, 0, cx, cy, w * r_f)
    grad.add_color_stop_rgb(0.0, *hex_rgb(c0))
    grad.add_color_stop_rgb(0.55, *hex_rgb(c1))
    grad.add_color_stop_rgb(1.0, *hex_rgb(c2))
    ctx.set_source(grad)
    ctx.rectangle(0, 0, w, h)
    ctx.fill()


def speed_lines(ctx, w, h, seed=7, n=26, color=(1, 1, 1)):
    random.seed(seed)
    ctx.save()
    ctx.set_line_width(3)
    for _ in range(n):
        y = random.uniform(-100, h + 100)
        length = random.uniform(220, 620)
        x = random.uniform(-200, w + 200)
        alpha = random.uniform(0.03, 0.07)
        ctx.set_source_rgba(*color, alpha)
        ctx.move_to(x, y)
        ctx.line_to(x - length * 0.45, y + length)
        ctx.stroke()
    ctx.restore()


# ---------------------------------------------------------------- GLITCH ---

def glitch_bolt_path(ctx, cx, cy, scale=1.0):
    pts = [
        (430, 190), (330, 420), (395, 420),
        (350, 610), (470, 380), (405, 380),
    ]
    pts = [(cx + (x - 400) * scale, cy + (y - 400) * scale) for x, y in pts]
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def draw_glitch_icon(ctx, cx, cy, scale=1.0):
    # chromatic-aberration ghost copies
    ctx.save()
    glitch_bolt_path(ctx, cx - 10 * scale, cy - 6 * scale, scale)
    ctx.set_source_rgba(*hex_rgb('ff2d95'), 0.55)
    ctx.fill()
    glitch_bolt_path(ctx, cx + 10 * scale, cy + 6 * scale, scale)
    ctx.set_source_rgba(*hex_rgb('00e5ff'), 0.55)
    ctx.fill()
    ctx.restore()

    glitch_bolt_path(ctx, cx, cy, scale)
    grad = cairo.LinearGradient(cx - 60 * scale, cy - 210 * scale, cx + 40 * scale, cy + 210 * scale)
    grad.add_color_stop_rgb(0.0, *hex_rgb('eaffff'))
    grad.add_color_stop_rgb(1.0, *hex_rgb('4de8ff'))
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.set_source_rgb(*hex_rgb('06121c'))
    ctx.set_line_width(6 * scale)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def glitch_profile():
    W = H = 800
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    bg_gradient(ctx, W, H, '1b7f99', '0c3446', '020608', cx_f=0.38, cy_f=0.32, r_f=0.9)
    draw_glitch_icon(ctx, 400, 400, scale=1.0)
    surface.write_to_png("glitch_profile.png")


def glitch_banner():
    W, H = 2560, 1440
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    bg_gradient(ctx, W, H, '18879e', '0b3446', '020508')
    speed_lines(ctx, W, H, seed=3, color=(0.6, 1, 1))

    draw_glitch_icon(ctx, 620, 720, scale=0.62)

    ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(128)
    text_x = 920
    baseline_y = 760
    ctx.set_source_rgba(0, 0, 0, 0.35)
    ctx.move_to(text_x + 6, baseline_y + 6)
    ctx.show_text("GLITCH")
    ctx.set_source_rgb(*hex_rgb('eafcff'))
    ctx.move_to(text_x, baseline_y)
    ctx.show_text("GLITCH")

    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(40)
    ctx.set_source_rgb(*hex_rgb('7be9ff'))
    ctx.move_to(text_x + 6, baseline_y + 74)
    ctx.show_text("T E C H .   D E C O D E D .")

    surface.write_to_png("glitch_banner.png")


# ---------------------------------------------------------- CAPITOL BUZZ ---

def draw_capitol_icon(ctx, cx, cy, scale=1.0):
    gold = hex_rgb('e8c46a')
    gold_dk = hex_rgb('b98f2e')
    navy_line = hex_rgb('14213d')

    def s(v):
        return cx + v * scale if False else v  # placeholder, unused

    # dome (half circle)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)

    grad = cairo.LinearGradient(0, -140, 0, 0)
    grad.add_color_stop_rgb(0.0, *hex_rgb('fbe7a1'))
    grad.add_color_stop_rgb(1.0, *gold_dk)

    ctx.arc(0, 0, 140, 3.14159, 2 * 3.14159)
    ctx.close_path()
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.set_source_rgb(*navy_line)
    ctx.set_line_width(6)
    ctx.stroke()

    # base block
    ctx.rectangle(-140, 0, 280, 90)
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.set_source_rgb(*navy_line)
    ctx.set_line_width(6)
    ctx.stroke()

    # columns (simple ticks) on base
    ctx.set_source_rgba(*navy_line, 0.55)
    ctx.set_line_width(5)
    for i in range(-5, 6):
        x = i * 22
        ctx.move_to(x, 6)
        ctx.line_to(x, 84)
        ctx.stroke()

    # spire
    ctx.set_source_rgb(*gold_dk)
    ctx.set_line_width(8)
    ctx.move_to(0, -140)
    ctx.line_to(0, -190)
    ctx.stroke()
    ctx.arc(0, -196, 8, 0, 2 * 3.14159)
    ctx.set_source_rgb(*hex_rgb('fbe7a1'))
    ctx.fill()

    ctx.restore()

    # "buzz" arcs to the right
    ctx.save()
    ctx.set_source_rgba(*hex_rgb('fbe7a1'), 0.8)
    ctx.set_line_width(5 * scale)
    for i, r in enumerate((40, 65, 90)):
        ctx.arc(cx + 150 * scale, cy - 30 * scale, r * scale, -0.5, 0.5)
        ctx.stroke()
    ctx.restore()


def capitol_profile():
    W = H = 800
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    bg_gradient(ctx, W, H, '1d3a68', '13233f', '060a14', cx_f=0.4, cy_f=0.34, r_f=0.9)
    draw_capitol_icon(ctx, 400, 430, scale=1.35)
    surface.write_to_png("capitol_profile.png")


def capitol_banner():
    W, H = 2560, 1440
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    bg_gradient(ctx, W, H, '1d3a68', '122036', '05070d')
    speed_lines(ctx, W, H, seed=11, color=(0.85, 0.75, 0.5))

    draw_capitol_icon(ctx, 650, 760, scale=0.85)

    ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(120)
    text_x = 950
    baseline_y = 760
    ctx.set_source_rgba(0, 0, 0, 0.35)
    ctx.move_to(text_x + 6, baseline_y + 6)
    ctx.show_text("CAPITOL BUZZ")
    ctx.set_source_rgb(*hex_rgb('f5f0e2'))
    ctx.move_to(text_x, baseline_y)
    ctx.show_text("CAPITOL BUZZ")

    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(38)
    ctx.set_source_rgb(*hex_rgb('e8c46a'))
    ctx.move_to(text_x + 6, baseline_y + 74)
    ctx.show_text("P O L I T I C S .   P L A I N L Y .")

    surface.write_to_png("capitol_banner.png")


if __name__ == "__main__":
    glitch_profile()
    glitch_banner()
    capitol_profile()
    capitol_banner()
    print("done")
