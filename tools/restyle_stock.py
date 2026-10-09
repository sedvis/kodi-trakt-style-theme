"""Redraw Estuary's stock 9-slice textures in the Trakt style (rounded corners, ink surfaces).

Canvas sizes and margins stay identical to Estuary's so every existing border="" value keeps working.
"""
import os
from PIL import Image, ImageDraw, ImageFilter

MEDIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "media")
SS = 4


def rr(size, box, radius, fill, shadow=0):
    w, h = size
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([c * SS for c in box], radius=radius * SS, fill=(0, 0, 0, shadow))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(6 * SS)))
    ImageDraw.Draw(img).rounded_rectangle([c * SS for c in box], radius=radius * SS, fill=fill)
    return img.resize((w, h), Image.LANCZOS)


def save(rel, img):
    img.save(os.path.join(MEDIA, rel), optimize=True)


# 80x80 canvases with a 20px margin -> inner box 20..59.
INNER = (20, 20, 59, 59)
save("buttons/button-fo.png", rr((80, 80), INNER, 12, (255, 255, 255, 255)))
save("buttons/button-nofo.png", rr((80, 80), INNER, 12, (32, 30, 35, 210)))
save("buttons/dialogbutton-fo.png", rr((80, 80), INNER, 12, (255, 255, 255, 255)))
save("buttons/dialogbutton-nofo.png", rr((80, 80), INNER, 12, (47, 45, 51, 170)))
save("buttons/button-alt-nofo.png", rr((80, 80), INNER, 12, (255, 255, 255, 30)))
save("dialogs/dialog-bg.png", rr((80, 80), INNER, 16, (32, 30, 35, 245), shadow=120))
save("dialogs/dialog-bg-nobo.png", Image.new("RGBA", (40, 40), (32, 30, 35, 245)))
save("overlays/shadow.png", rr((80, 80), INNER, 14, (0, 0, 0, 0), shadow=110))
# Thumbnail focus ring (20x20, border 8) -> rounded ring.
ring = Image.new("RGBA", (20 * SS, 20 * SS), (0, 0, 0, 0))
d = ImageDraw.Draw(ring)
d.rounded_rectangle([0, 0, 20 * SS - 1, 20 * SS - 1], radius=7 * SS, fill=(255, 255, 255, 255))
d.rounded_rectangle([4 * SS, 4 * SS, 16 * SS - 1, 16 * SS - 1], radius=3 * SS, fill=(0, 0, 0, 0))
save("buttons/thumbnail_focused.png", ring.resize((20, 20), Image.LANCZOS))
# List focus bar: now a 9-slice (the XML gets border="12").
save("lists/focus.png", rr((64, 64), (0, 0, 63, 63), 12, (255, 255, 255, 255)))
print("stock textures restyled")
