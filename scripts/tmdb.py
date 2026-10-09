# Trakt Style: small TMDB helper shared by the skin scripts (person.py, trailer.py).
# Uses the TMDB API key from Elementum's settings; builds Elementum-style list items.
import json
import urllib.parse
import urllib.request

import xbmc
import xbmcaddon
import xbmcgui

E = "plugin://plugin.video.elementum"
API = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/"
KEY_HINT = ("This needs a TMDB API key.[CR]"
            "Enter yours in Elementum > Settings > Advanced > TheMovieDB > API key.")


def api_key():
    try:
        return xbmcaddon.Addon("plugin.video.elementum").getSetting("tmdb_api_key").strip()
    except RuntimeError:
        return ""


def get(path, key, **params):
    params.update(api_key=key, language="en-US")
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def image(path, size):
    return f"{IMG}{size}{path}" if path else ""


def year(date):
    return (date or "")[:4]


def names(people, limit=15):
    return [p.get("name") for p in (people or [])[:limit] if p.get("name")]


def youtube_trailer(videos):
    clips = [v for v in (videos or {}).get("results") or [] if v.get("site") == "YouTube" and v.get("key")]
    clips.sort(key=lambda v: (v.get("type") != "Trailer", not v.get("official"), v.get("published_at") or ""))
    return f"plugin://plugin.video.youtube/play/?video_id={clips[0]['key']}" if clips else ""


def details_listitem(media_type, tmdb_id, key):
    """A full Elementum-style item for a movie ("movie") or show ("tv"), for Kodi's info page."""
    if media_type == "movie":
        d = get(f"/movie/{tmdb_id}", key, append_to_response="credits,videos")
        title, date = d.get("title") or "", d.get("release_date") or ""
        label = f"{title} ({year(date)})" if year(date) else title
        path = f"{E}/movie/{d['id']}/links/{urllib.parse.quote(label)}"
        mediatype = "movie"
    else:
        d = get(f"/tv/{tmdb_id}", key, append_to_response="credits,videos")
        title, date = d.get("name") or "", d.get("first_air_date") or ""
        path = f"{E}/show/{d['id']}/seasons"
        mediatype = "tvshow"

    item = xbmcgui.ListItem(title, path=path, offscreen=True)
    item.setIsFolder(mediatype == "tvshow")
    if mediatype == "movie":
        item.setProperty("IsPlayable", "true")
    item.setArt({
        "poster": image(d.get("poster_path"), "w500"),
        "thumb": image(d.get("poster_path"), "w500"),
        "fanart": image(d.get("backdrop_path"), "w1280"),
    })
    tag = item.getVideoInfoTag()
    tag.setMediaType(mediatype)
    tag.setTitle(title)
    tag.setOriginalTitle(d.get("original_title") or d.get("original_name") or title)
    tag.setPlot(d.get("overview") or "")
    tag.setTagLine(d.get("tagline") or "")
    if year(date):
        tag.setYear(int(year(date)))
        tag.setPremiered(date)
        tag.setFirstAired(date)
    tag.setGenres([g["name"] for g in d.get("genres") or []])
    tag.setStudios(names(d.get("production_companies") or d.get("networks"), 3))
    tag.setCountries([c.get("name") for c in d.get("production_countries") or [] if c.get("name")])
    if d.get("vote_average"):
        tag.setRating(float(d["vote_average"]), int(d.get("vote_count") or 0), "themoviedb", True)
    if mediatype == "movie" and d.get("runtime"):
        tag.setDuration(int(d["runtime"]) * 60)
    if mediatype == "tvshow":
        tag.setTvShowStatus(d.get("status") or "")
        item.setProperty("totalseasons", str(d.get("number_of_seasons") or ""))
        item.setProperty("totalepisodes", str(d.get("number_of_episodes") or ""))
    trailer = youtube_trailer(d.get("videos"))
    if trailer:
        tag.setTrailer(trailer)
    crew = (d.get("credits") or {}).get("crew") or []
    tag.setDirectors([p["name"] for p in crew if p.get("job") == "Director"]
                     or [p["name"] for p in d.get("created_by") or []])
    tag.setWriters([p["name"] for p in crew if p.get("department") == "Writing"][:5])
    tag.setCast([xbmc.Actor(p.get("name") or "", p.get("character") or "", i, image(p.get("profile_path"), "w185"))
                 for i, p in enumerate(((d.get("credits") or {}).get("cast") or [])[:30])])
    tag.setUniqueIDs({"tmdb": str(d["id"])}, "tmdb")
    return item


def show_info(item):
    """Replace the current info page (if any) with the given item's."""
    xbmc.executebuiltin("Dialog.Close(movieinformation,true)")
    xbmc.sleep(200)
    xbmcgui.Dialog().info(item)
