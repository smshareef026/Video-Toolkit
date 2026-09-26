import sys
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

svg_path = sys.argv[1]
png_path = sys.argv[2]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0

drawing = svg2rlg(svg_path)
if scale != 1.0:
    drawing.width *= scale
    drawing.height *= scale
    drawing.scale(scale, scale)

renderPM.drawToFile(drawing, png_path, fmt="PNG", bg=0x000000)
print("wrote", png_path)
