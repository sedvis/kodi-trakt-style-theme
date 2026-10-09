# Trakt Style: filmography of an actor or director from the info page, via TMDB.
#
# Kodi's own cast / director search only looks in the local video library, where Elementum
# items are not. This looks the person up on TMDB (with the API key from Elementum's settings),
# lists their movies and shows newest first, and opens the chosen one as an Elementum item: the
# info page with Play (movies) or Play / Browse (shows), like the home rows.
#
# RunScript(special://skin/scripts/person.py,cast,<name>)
# RunScript(special://skin/scripts/person.py,director,<name> / <name>)
import sys

import xbmc
import xbmcgui
import xbmcvfs

sys.path.insert(0, xbmcvfs.translatePath("special://skin/scripts/"))
import tmdb  # noqa: E402

# TMDB TV genres that are mostly appearances as themselves: news, reality, talk.
NOISE_TV_GENRES = {10763, 10764, 10767}


def find_person(name, role, key):
    results = tmdb.get("/search/person", key, query=name, include_adult="false").get("results") or []
    department = "Directing" if role == "director" else "Acting"
    exact = [p for p in results if p.get("name", "").lower() == name.lower()]
    for group in (exact, results):
        for person in group:
            if person.get("known_for_department") == department:
                return person
        if group:
            return group[0]
    return None


def release(c):
    return c.get("release_date") or c.get("first_air_date") or ""


def filmography(person_id, role, key):
    credits = tmdb.get(f"/person/{person_id}/combined_credits", key)
    if role == "director":
        entries = [c for c in credits.get("crew") or [] if c.get("job") == "Director"]
    else:
        entries = [c for c in credits.get("cast") or []
                   if not (c.get("media_type") == "tv" and NOISE_TV_GENRES & set(c.get("genre_ids") or []))
                   and "self" not in (c.get("character") or "").lower()]
    seen, works = set(), []
    for c in entries:
        # TMDB sometimes lists the same title twice (e.g. an extended cut with its own id).
        same_title = ((c.get("title") or c.get("name") or "").lower(), release(c))
        ident = (c.get("media_type"), c.get("id"))
        if ident in seen or same_title in seen or c.get("media_type") not in ("movie", "tv"):
            continue
        seen.update((ident, same_title))
        works.append(c)
    # Newest first; titles without a date (not yet scheduled) at the end.
    works.sort(key=lambda c: (bool(release(c)), release(c)), reverse=True)
    return works


def work_listitem(c, role):
    is_movie = c["media_type"] == "movie"
    title = c.get("title") or c.get("name") or ""
    label = f"{title} ({tmdb.year(release(c))})" if tmdb.year(release(c)) else title
    kind = "Movie" if is_movie else "TV show"
    detail = c.get("character") if role != "director" else ""
    item = xbmcgui.ListItem(label, f"{kind}  •  {detail}" if detail else kind)
    item.setArt({"thumb": tmdb.image(c.get("poster_path"), "w185"),
                 "poster": tmdb.image(c.get("poster_path"), "w185")})
    return item


def main():
    role = sys.argv[1] if len(sys.argv) > 1 else "cast"
    raw = sys.argv[2] if len(sys.argv) > 2 else ""
    people = [n.strip() for n in raw.split(" / ") if n.strip()]
    if not people:
        return
    key = tmdb.api_key()
    if not key:
        xbmcgui.Dialog().ok("Trakt Style", "Searching by actor or director: " + tmdb.KEY_HINT)
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
        item = tmdb.details_listitem(works[choice]["media_type"], works[choice]["id"], key)
    except Exception as error:
        xbmc.log(f"Trakt Style details failed: {error}", xbmc.LOGWARNING)
        item = None
    finally:
        xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
    if item is None:
        xbmcgui.Dialog().notification("Trakt Style", "Could not load the details from TMDB", xbmcgui.NOTIFICATION_ERROR)
        return
    tmdb.show_info(item)


main()
