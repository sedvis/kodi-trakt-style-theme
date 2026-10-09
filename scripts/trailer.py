# Trakt Style: play the trailer from the info page and come back to the same info page.
#
# Kodi's own trailer button (11) closes the info page before playing (a modal dialog would block
# the fullscreen video) and never reopens it, so stopping the trailer drops you on Home. This
# does the same, waits for the trailer to end or be stopped, then reopens the page: with
# Action(Info) when the item is still the focused one underneath (rows, Elementum lists), or
# rebuilt from TMDB for pages opened from a filmography.
#
# RunScript(special://skin/scripts/trailer.py,<trailer>,<item path>,<dbtype>,<tmdb id>)
import sys

import xbmc
import xbmcgui
import xbmcvfs

sys.path.insert(0, xbmcvfs.translatePath("special://skin/scripts/"))
import tmdb  # noqa: E402


def wait(condition, seconds, monitor):
    """Wait until condition() is true; False on timeout or when Kodi is shutting down."""
    for _ in range(int(seconds * 10)):
        if condition():
            return True
        if monitor.waitForAbort(0.1):
            return False
    return condition()


def reopen(path, dbtype, tmdb_id):
    if path and xbmc.getInfoLabel("ListItem.FileNameAndPath") == path:
        xbmc.executebuiltin("Action(Info)")
        return
    key = tmdb.api_key()
    if not (tmdb_id and key and dbtype in ("movie", "tvshow")):
        return
    try:
        item = tmdb.details_listitem("movie" if dbtype == "movie" else "tv", tmdb_id, key)
    except Exception as error:
        xbmc.log(f"Trakt Style trailer: could not rebuild the info page: {error}", xbmc.LOGWARNING)
        return
    tmdb.show_info(item)


def main():
    args = sys.argv[1:] + [""] * 4
    trailer, path, dbtype, tmdb_id = args[:4]
    if not trailer:
        return
    monitor, player = xbmc.Monitor(), xbmc.Player()

    xbmc.executebuiltin("Dialog.Close(movieinformation,true)")
    xbmc.sleep(200)
    xbmc.executebuiltin(f'PlayMedia("{trailer}")')

    # YouTube and friends can take a while to resolve; give up after 30s and just go back.
    if wait(lambda: player.isPlayingVideo(), 30, monitor):
        wait(lambda: not player.isPlaying(), 6 * 60 * 60, monitor)
    if monitor.abortRequested():
        return
    wait(lambda: not xbmc.getCondVisibility("Window.IsActive(fullscreenvideo)"), 5, monitor)
    xbmc.sleep(300)
    reopen(path, dbtype, tmdb_id)


main()
