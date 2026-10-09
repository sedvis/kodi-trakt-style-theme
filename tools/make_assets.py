"""Generate the Trakt Style skin textures: icons, masks, 9-slice frames, gradients, backgrounds.

Usage: python tools/make_assets.py <lucide.ttf> <lucide-info.json> <Roboto-Bold.ttf>
Writes into media/trakt, extras/backgrounds and resources (the skin lives at the repository root).
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MEDIA = os.path.join(ROOT, "media", "trakt")
SS = 4  # supersampling factor for anti-aliased shapes

BG = (0x17, 0x14, 0x1A)
PURPLE = (0x9F, 0x42, 0xC6)
PURPLE_LIGHT = (0xB4, 0x5F, 0xD9)
PURPLE_DARK = (0x8D, 0x35, 0xB1)


def out(name, img):
    path = os.path.join(MEDIA, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


def rounded_rect(w, h, r, fill=(255, 255, 255, 255), stroke=0):
    """White rounded rectangle (filled, or a ring when stroke > 0), anti-aliased."""
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    if stroke:
        d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=r * SS, fill=fill)
        s = stroke * SS
        d.rounded_rectangle([s, s, w * SS - 1 - s, h * SS - 1 - s], radius=max(0, (r - stroke)) * SS, fill=(0, 0, 0, 0))
    else:
        d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=r * SS, fill=fill)
    return big.resize((w, h), Image.LANCZOS)


def circle(size, fill=(255, 255, 255, 255), stroke=0):
    big = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.ellipse([0, 0, size * SS - 1, size * SS - 1], fill=fill)
    if stroke:
        s = stroke * SS
        d.ellipse([s, s, size * SS - 1 - s, size * SS - 1 - s], fill=(0, 0, 0, 0))
    return big.resize((size, size), Image.LANCZOS)


def star_polygon(cx, cy, r_out, r_in, points=5, rot=-90):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / points)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def icons(lucide_ttf, info_json):
    info = json.load(open(info_json, encoding="utf8"))
    names = {
        # file name: lucide glyph
        "search": "search", "home": "house", "discover": "sparkles", "lists": "list",
        "settings": "settings", "star": "star", "heart": "heart", "check": "check",
        "checks": "check-check", "bookmark": "bookmark", "bookmark-plus": "bookmark-plus",
        "play": "play", "trailer": "circle-play", "chevron-right": "chevron-right",
        "chevron-left": "chevron-left", "section": "circle-chevron-up", "more": "ellipsis-vertical",
        "calendar": "calendar-days", "flame": "flame", "trending": "trending-up", "users": "users",
        "user": "user", "clock": "clock", "power": "power", "info": "info", "close": "x",
        "movies": "clapperboard", "shows": "tv", "media": "monitor-play", "filter": "list-filter",
        "menu": "menu", "history": "history", "library": "library", "plus": "plus",
        "refresh": "refresh-cw", "folder": "folder", "music": "music", "pictures": "image",
        "games": "gamepad-2", "livetv": "radio", "weather": "cloud", "magnet": "magnet",
        "download": "download", "eye": "eye", "popcorn": "popcorn", "compass": "compass",
        "addons": "layout-grid", "favourites": "star", "timer": "timer", "calendar-clock": "calendar-clock",
        "trophy": "trophy", "zap": "zap", "video": "video", "users-round": "users-round",
        # player (OSD)
        "osd-prev": "skip-back", "osd-next": "skip-forward", "osd-rew": "rewind", "osd-ff": "fast-forward",
        "osd-stop": "square", "osd-subtitles": "captions", "osd-settings": "settings-2",
        "osd-bookmarks": "bookmark", "osd-info": "info", "osd-playlist": "list-video", "osd-channels": "tv",
        "osd-guide": "calendar-days", "osd-menu": "house", "osd-teletext": "text", "osd-3d": "box",
        "osd-record": "circle-dot", "osd-audio": "audio-lines", "osd-volume-mute": "volume-x",
        # Elementum menus (picked by the entry's path in Includes_Trakt.xml TraktMenuIcon)
        "menu-movies": "clapperboard", "menu-shows": "tv", "menu-search": "search",
        "menu-torrents": "cloud-download", "menu-addtorrent": "link", "menu-history": "history",
        "menu-providers": "shield-check", "menu-changelog": "file-text", "menu-status": "activity",
        "menu-donate": "heart", "menu-settings": "settings", "menu-provider-settings": "sliders-horizontal",
        "menu-lists": "list", "menu-watchlist": "bookmark", "menu-collection": "library",
        "menu-calendar": "calendar-days", "menu-recommended": "sparkles", "menu-toplists": "trophy",
        "menu-trending": "trending-up", "menu-popular": "flame", "menu-played": "circle-play",
        "menu-watched": "eye", "menu-collected": "archive", "menu-anticipated": "hourglass",
        "menu-boxoffice": "ticket", "menu-top": "star", "menu-voted": "thumbs-up", "menu-recent": "clock",
        "menu-imdb": "award", "menu-genres": "drama", "menu-languages": "languages", "menu-countries": "globe",
        "menu-library": "hard-drive", "menu-elementum-library": "folder-heart", "menu-progress": "list-video",
        "menu-episodes": "tv-minimal-play", "menu-premieres": "calendar-plus", "menu-magnet": "magnet",
        "menu-folder": "folder", "menu-past-search": "history",
    }
    size = 128
    font = ImageFont.truetype(lucide_ttf, 112)
    for fname, glyph in names.items():
        code = info[glyph]["encodedCode"].lstrip("\\")
        ch = chr(int(code, 16))
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        bbox = d.textbbox((0, 0), ch, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), ch, font=font, fill=(255, 255, 255, 255))
        out(f"icons/{fname}.png", img)

    # Filled star (Trakt rating star) and filled heart / check badge.
    big = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = size * SS / 2
    d.polygon(star_polygon(c, c * 1.06, c * 0.92, c * 0.40), fill=(255, 255, 255, 255))
    out("icons/star-filled.png", big.resize((size, size), Image.LANCZOS))

    big = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    s = size * SS
    d.ellipse([s * 0.08, s * 0.14, s * 0.52, s * 0.58], fill="white")
    d.ellipse([s * 0.48, s * 0.14, s * 0.92, s * 0.58], fill="white")
    d.polygon([(s * 0.10, s * 0.45), (s * 0.90, s * 0.45), (s * 0.5, s * 0.90)], fill="white")
    out("icons/heart-filled.png", big.resize((size, size), Image.LANCZOS))

    # Filled play / pause for the big OSD button.
    big = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    s4 = size * SS
    d.rounded_rectangle([s4 * 0.24, s4 * 0.14, s4 * 0.40, s4 * 0.86], radius=s4 * 0.05, fill="white")
    d.rounded_rectangle([s4 * 0.60, s4 * 0.14, s4 * 0.76, s4 * 0.86], radius=s4 * 0.05, fill="white")
    out("icons/osd-pause-filled.png", big.resize((size, size), Image.LANCZOS))
    big = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.polygon([(s4 * 0.28, s4 * 0.12), (s4 * 0.28, s4 * 0.88), (s4 * 0.88, s4 * 0.50)], fill="white")
    out("icons/osd-play-filled.png", big.resize((size, size), Image.LANCZOS))


def masks():
    out("masks/poster.png", rounded_rect(400, 600, 22))
    out("masks/poster-lg.png", rounded_rect(400, 600, 14))
    out("masks/landscape.png", rounded_rect(640, 360, 22))
    out("masks/landscape-lg.png", rounded_rect(640, 360, 12))
    out("masks/square.png", rounded_rect(400, 400, 26))
    out("masks/circle.png", circle(256))
    out("masks/portrait.png", rounded_rect(300, 440, 20))  # cast cards (Trakt uses ~3:4.4)


def frames():
    # 9-slice fills: use border = radius + 2 in skin XML.
    for r in (8, 12, 16, 20, 24):
        out(f"frames/rr{r}.png", rounded_rect(r * 2 + 16, r * 2 + 16, r))
    # Focus rings (stroke) for cards: border = radius + 2.
    for r, s in ((14, 4), (18, 5), (24, 5)):
        out(f"frames/ring{r}.png", rounded_rect(r * 2 + 16, r * 2 + 16, r, stroke=s))
    # Pills: full radius, texture height == display height so corners stay round.
    for h in (8, 12, 28, 32, 36, 40, 44, 48, 56, 64, 72):
        out(f"frames/pill{h}.png", rounded_rect(h + 16, h, h // 2))
        out(f"frames/pill{h}-ring.png", rounded_rect(h + 16, h, h // 2, stroke=3))
    out("frames/circle-ring.png", circle(128, stroke=6))
    out("frames/circle.png", circle(128))
    # Slider nibs are drawn at the texture's own pixel size, so they get dedicated small files.
    out("frames/nib.png", circle(26))
    out("frames/nib-lg.png", circle(34))
    # Kodi scales slider nibs by control height / bar texture height: a 26px bar keeps nibs 1:1.
    out("frames/sliderbar26.png", Image.new("RGBA", (8, 26), (255, 255, 255, 255)))
    out("frames/white.png", Image.new("RGBA", (8, 8), (255, 255, 255, 255)))
    # Narrow marker for chapter ticks on the player bar (ranges controls keep the texture's aspect).
    out("frames/tick.png", Image.new("RGBA", (2, 8), (255, 255, 255, 255)))


def gradients():
    def vgrad(h, a0, a1, w=8, power=1.0):
        img = Image.new("RGBA", (w, h))
        px = img.load()
        for y in range(h):
            t = (y / (h - 1)) ** power
            a = round(a0 + (a1 - a0) * t)
            for x in range(w):
                px[x, y] = (255, 255, 255, a)
        return img

    out("gradients/bottom.png", vgrad(512, 0, 255, power=1.4))         # transparent -> solid
    out("gradients/top.png", vgrad(512, 255, 0, power=0.7))            # solid -> transparent
    out("gradients/card-bottom.png", vgrad(256, 0, 230, power=1.6))    # thumbnail legibility
    # left.png: solid at the left edge fading to transparent; right.png is its mirror.
    out("gradients/left.png", vgrad(512, 255, 0, power=0.9).rotate(90, expand=True))
    out("gradients/right.png", vgrad(512, 255, 0, power=0.9).rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT))

    # Purple accent gradient (Trakt badge/button: 135deg purple-400 -> purple-600).
    w, h = 256, 64
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = min(1.0, max(0.0, (x / w * 0.8 + y / h * 0.2)))
            px[x, y] = tuple(round(PURPLE_LIGHT[i] + (PURPLE_DARK[i] - PURPLE_LIGHT[i]) * t) for i in range(3)) + (255,)
    out("gradients/accent.png", img)


def radial_glow(w, h, cx, cy, radius, color, strength):
    """Soft radial glow layer (RGBA) used for backgrounds."""
    small = Image.new("RGBA", (w // 8, h // 8), color + (0,))
    px = small.load()
    for y in range(small.height):
        for x in range(small.width):
            dx, dy = (x * 8 - cx) / radius, (y * 8 - cy) / radius
            d = math.sqrt(dx * dx + dy * dy)
            a = max(0.0, 1.0 - d) ** 2 * strength
            px[x, y] = color + (round(a * 255),)
    return small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))


def backgrounds():
    # White radial glow; the skin tints it with the theme's accent_deep colour over the flat ink fill.
    out("gradients/glow-tl.png", radial_glow(1920, 1080, 200, 0, 1300, (255, 255, 255), 1.0))


def badges(bold_ttf):
    """IMDb-style badge and small 'TMDB'/'Trakt' text badges, drawn as plain text on rounded rects."""
    def text_badge(name, text, fg, bgc, h=48, pad=12, size=30):
        font = ImageFont.truetype(bold_ttf, size * SS)
        tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bb = tmp.textbbox((0, 0), text, font=font)
        tw = (bb[2] - bb[0]) // SS
        w = tw + pad * 2
        big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=8 * SS, fill=bgc)
        d.text(((w * SS - (bb[2] - bb[0])) / 2 - bb[0], (h * SS - (bb[3] - bb[1])) / 2 - bb[1]), text, font=font, fill=fg)
        out(f"badges/{name}.png", big.resize((w, h), Image.LANCZOS))

    text_badge("imdb", "IMDb", (0, 0, 0, 255), (0xF5, 0xC5, 0x18, 255))
    text_badge("tmdb", "TMDB", (0x0D, 0x25, 0x3F, 255), (0x01, 0xB4, 0xE4, 255))


def skin_icon():
    """Add-on icon/fanart: purple gradient tile with a play glyph (original artwork, not Trakt's logo)."""
    s = 512
    big = Image.new("RGBA", (s * SS, s * SS), (0, 0, 0, 0))
    grad = Image.new("RGBA", (s * SS, s * SS))
    gp = grad.load()
    for y in range(0, s * SS, SS):
        for x in range(0, s * SS, SS):
            t = (x + y) / (2 * s * SS)
            c = tuple(round(PURPLE_LIGHT[i] + (PURPLE_DARK[i] - PURPLE_LIGHT[i]) * t) for i in range(3)) + (255,)
            for yy in range(SS):
                for xx in range(SS):
                    gp[x + xx, y + yy] = c
    mask = Image.new("L", (s * SS, s * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s * SS - 1, s * SS - 1], radius=110 * SS, fill=255)
    big.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(big)
    c = s * SS / 2
    r = s * SS * 0.24
    d.polygon([(c - r * 0.75, c - r), (c - r * 0.75, c + r), (c + r * 1.05, c)], fill=(255, 255, 255, 255))
    icon = big.resize((s, s), Image.LANCZOS)
    icon.save(os.path.join(ROOT, "resources", "icon.png"), optimize=True)

    fan = Image.new("RGBA", (1920, 1080), BG + (255,))
    fan.alpha_composite(radial_glow(1920, 1080, 0, 0, 1300, (0x3F, 0x12, 0x51), 0.7))
    fan.alpha_composite(icon.resize((320, 320), Image.LANCZOS), (800, 380))
    fan.convert("RGB").save(os.path.join(ROOT, "resources", "fanart.jpg"), quality=90)


if __name__ == "__main__":
    lucide_ttf, info_json, bold_ttf = sys.argv[1:4]
    icons(lucide_ttf, info_json)
    masks()
    frames()
    gradients()
    backgrounds()
    badges(bold_ttf)
    skin_icon()
    print("assets written to", MEDIA)
