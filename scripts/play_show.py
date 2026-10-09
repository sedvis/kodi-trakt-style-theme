# Trakt Style: "Play" on an Elementum TV show's info page.
#
# Plays the show's next episode from Elementum's Trakt progress (the same item Continue Watching
# would play); when the show is not in progress (or Trakt is not connected), plays the first
# episode of the first regular season. Elementum has no "next episode" route of its own.
#
# RunScript(special://skin/scripts/play_show.py,<tmdb id>,<show path>)
import json
import re
import sys

import xbmc

E = "plugin://plugin.video.elementum"


def rpc(method, **params):
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    return json.loads(xbmc.executeJSONRPC(json.dumps(request))).get("result") or {}


def listing(path):
    result = rpc("Files.GetDirectory", directory=path, media="video", properties=["season", "episode"])
    return result.get("files") or []


def show_id(args):
    for arg in args:
        if arg.isdigit():
            return arg
        m = re.search(r"/show/(\d+)", arg)
        if m:
            return m.group(1)
    return None


def next_from_progress(tmdb):
    if not xbmc.getCondVisibility("!String.IsEmpty(Addon.SettingStr(plugin.video.elementum,trakt_token))"):
        return None
    marker = f"/show/{tmdb}/season/"
    for item in listing(f"{E}/shows/trakt/progress"):
        if item.get("filetype") == "file" and marker in item.get("file", ""):
            return item["file"]
    return None


def first_episode(tmdb):
    seasons = [s for s in listing(f"{E}/show/{tmdb}/seasons")
               if s.get("filetype") == "directory" and (s.get("season") or 0) >= 1]
    for season in sorted(seasons, key=lambda s: s["season"]):
        episodes = [e for e in listing(season["file"]) if e.get("filetype") == "file"]
        if episodes:
            return min(episodes, key=lambda e: e.get("episode") or 0)["file"]
    return None


def main():
    tmdb = show_id(sys.argv[1:])
    if not tmdb:
        return
    xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
    try:
        target = (next_from_progress(tmdb) or first_episode(tmdb)
                  or f"{E}/show/{tmdb}/season/1/episode/1/links")
    finally:
        xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
    xbmc.executebuiltin("Dialog.Close(movieinformation)")
    xbmc.executebuiltin(f'PlayMedia("{target}")')


main()
