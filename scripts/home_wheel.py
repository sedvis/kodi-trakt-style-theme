# Trakt Style: make the mouse wheel / touchpad scroll the home screen rows vertically.
#
# Kodi containers always consume mouse-wheel events (CGUIBaseContainer::OnMouseEvent ->
# Scroll()), so with the pointer over a horizontal home row the wheel scrolls that row and
# never reaches the vertical grouplist. Skin XML cannot change that, but a keymap can: on
# the Home window the wheel is mapped to Up/Down, which moves focus row to row (the rows
# themselves still scroll sideways with Left/Right). Mouse hover and click are unchanged.
#
# Run from the skin: RunScript(special://skin/scripts/home_wheel.py)
# Installs the keymap unless Skin.HasSetting(home_wheel_rows) is set, otherwise removes it.
import xbmc
import xbmcgui
import xbmcvfs

KEYMAP = "special://profile/keymaps/skin.traktstyle-home-wheel.xml"
CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Written by the Trakt Style skin (skin.traktstyle): on the home screen the mouse wheel
     moves between rows instead of scrolling a row sideways. Turn it off in
     Skin settings > Home screen, or delete this file. -->
<keymap>
	<Home>
		<mouse>
			<wheelup>Up</wheelup>
			<wheeldown>Down</wheeldown>
		</mouse>
	</Home>
</keymap>
"""


def read(path):
    if not xbmcvfs.exists(path):
        return None
    f = xbmcvfs.File(path)
    try:
        return f.read()
    finally:
        f.close()


def main():
    # Home.xml only runs this once per session (see its onload).
    xbmcgui.Window(10000).setProperty("trakt_wheel_synced", "1")
    wanted = not xbmc.getCondVisibility("Skin.HasSetting(home_wheel_rows)")
    current = read(KEYMAP)
    if wanted and current != CONTENT:
        xbmcvfs.mkdirs("special://profile/keymaps/")
        f = xbmcvfs.File(KEYMAP, "w")
        try:
            f.write(CONTENT)
        finally:
            f.close()
    elif not wanted and current is not None:
        xbmcvfs.delete(KEYMAP)
    else:
        return
    xbmc.executebuiltin("Action(reloadkeymaps)")


main()
