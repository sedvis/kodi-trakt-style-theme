# Trakt Style: filmography of an actor or director from the info page, via TMDB.
#
# Kodi's own cast / director search only looks in the local video library, where Elementum
# items are not. This looks the person up on TMDB (with the API key from Elementum's settings),
# lists their movies and shows, and opens the chosen one as an Elementum item: the info page
# with Play (movies) or Play / Browse (shows), like the home rows.
#
# RunScript(special://skin/scripts/person.py,cast,<name>)
# RunScript(special://skin/scripts/person.py,director,<name> / <name>)
import json
import sys
import urllib.parse
import urllib.request

import xbmc
import xbmcaddon
import xbmcgui

E = "plugin://plugin.video.elementum"
API = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/"
# TMDB TV genres that are mostly appearances as themselves: news, reality, talk.
NOISE_TV_GENRES = {10763, 10764, 10767}


def api_key():
    try:
        return xbmcaddon.Addon("plugin.video.elementum").getSetting("tmdb_api_key").strip()
    except RuntimeError:
        return ""


def tmdb(path, key, **params):
    params.update(api_key=key, language="en-US")
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def image(path, size):
    return f"{IMG}{size}{path}" if path else ""


def year(date):
    return (date or "")[:4]


def find_person(name, role, key):
    results = tmdb("/search/person", key, query=name, include_adult="false").get("results") or []
    department = "Directing" if role == "director" else "Acting"
    exact = [p for p in results if p.get("name", "").lower() == name.lower()]
    for group in (exact, results):
        for person in group:
            if person.get("known_for_department") == department:
                return person
        if group:
            return group[0]
    return None


def filmography(person_id, role, key):
    credits = tmdb(f"/person/{person_id}/combined_credits", key)
    if role == "director":
        entries = [c for c in credits.get("crew") or [] if c.get("job") == "Director"]
    else:
        entries = [c for c in credits.get("cast") or []
                   if not (c.get("media_type") == "tv" and NOISE_TV_GENRES & set(c.get("genre_ids") or []))
                   and "self" not in (c.get("character") or "").lower()]
    seen, works = set(), []
    for c in entries:
        ident = (c.get("media_type"), c.get("id"))
        if ident in seen or c.get("media_type") not in ("movie", "tv"):
            continue
        seen.add(ident)
        works.append(c)
    # Best known first; cameos (a TV show for one or two episodes, uncredited parts) go last.
    def minor(c):
        return ((c.get("media_type") == "tv" and (c.get("episode_count") or 0) < 3)
                or "uncredited" in (c.get("character") or "").lower())
    works.sort(key=lambda c: (minor(c), -(c.get("vote_count") or 0)))
    return works


def work_listitem(c, role):
    is_movie = c["media_type"] == "movie"
    title = c.get("title") or c.get("name") or ""
    date = c.get("release_date") if is_movie else c.get("first_air_date")
    label = f"{title} ({year(date)})" if year(date) else title
    kind = "Movie" if is_movie else "TV show"
    detail = c.get("character") if role != "director" else ""
    item = xbmcgui.ListItem(label, f"{kind}  •  {detail}" if detail else kind)
    item.setArt({"thumb": image(c.get("poster_path"), "w185"), "poster": image(c.get("poster_path"), "w185")})
    return item


def names(people, limit=15):
    return [p.get("name") for p in (people or [])[:limit] if p.get("name")]


def details_listitem(c, key):
    """A full Elementum-style item for the chosen movie / show, for Kodi's info page."""
    if c["media_type"] == "movie":
        d = tmdb(f"/movie/{c['id']}", key, append_to_response="credits")
        title, date = d.get("title") or "", d.get("release_date") or ""
        label = f"{title} ({year(date)})" if year(date) else title
        path = f"{E}/movie/{d['id']}/links/{urllib.parse.quote(label)}"
        mediatype = "movie"
    else:
        d = tmdb(f"/tv/{c['id']}", key, append_to_response="credits")
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
    crew = (d.get("credits") or {}).get("crew") or []
    tag.setDirectors([p["name"] for p in crew if p.get("job") == "Director"]
                     or [p["name"] for p in d.get("created_by") or []])
    tag.setWriters([p["name"] for p in crew if p.get("department") == "Writing"][:5])
    tag.setCast([xbmc.Actor(p.get("name") or "", p.get("character") or "", i, image(p.get("profile_path"), "w185"))
                 for i, p in enumerate(((d.get("credits") or {}).get("cast") or [])[:30])])
    tag.setUniqueIDs({"tmdb": str(d["id"])}, "tmdb")
    return item


def main():
    role = sys.argv[1] if len(sys.argv) > 1 else "cast"
    raw = sys.argv[2] if len(sys.argv) > 2 else ""
    people = [n.strip() for n in raw.split(" / ") if n.strip()]
    if not people:
        return
    key = api_key()
    if not key:
        xbmcgui.Dialog().ok("Trakt Style", "Searching by actor or director needs a TMDB API key.[CR]"
                            "Enter yours in Elementum > Settings > Advanced > TheMovieDB > API key.")
        return
    name = people[0]
    if len(people) > 1:
        choice = xbmcgui.Dialog().select("Directors", people)
        if choice < 0:
            return
        name = people[choice]

    xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
    try:
        person = find_person(name, role, key)
        works = filmography(person["id"], role, key) if person else []
    except Exception as error:  # network / API errors
        xbmc.log(f"Trakt Style person search failed for {name!r}: {error}", xbmc.LOGWARNING)
        works, person = None, None
    finally:
        xbmc.executebuiltin("Dialog.Close(busydialognocancel)")

    if works is None:
        xbmcgui.Dialog().notification("Trakt Style", "TMDB search failed (check the API key)", xbmcgui.NOTIFICATION_ERROR)
        return
    if not works:
        xbmcgui.Dialog().notification("Trakt Style", f"Nothing found on TMDB for {name}", xbmcgui.NOTIFICATION_INFO)
        return

    heading = f"{person['name']}  •  {'Directed' if role == 'director' else 'Filmography'}"
    choice = xbmcgui.Dialog().select(heading, [work_listitem(c, role) for c in works], useDetails=True)
    if choice < 0:
        return

    xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
    try:
        item = details_listitem(works[choice], key)
    except Exception as error:
        xbmc.log(f"Trakt Style details failed: {error}", xbmc.LOGWARNING)
        item = None
    finally:
        xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
    if item is None:
        xbmcgui.Dialog().notification("Trakt Style", "Could not load the details from TMDB", xbmcgui.NOTIFICATION_ERROR)
        return
    # Replace the current info page with the chosen title's.
    xbmc.executebuiltin("Dialog.Close(movieinformation,true)")
    xbmc.sleep(200)
    xbmcgui.Dialog().info(item)


main()
