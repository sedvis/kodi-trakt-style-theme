"""Build the installable skin zip and the Kodi repository site.

    python build.py

Writes to dist/:
  skin.traktstyle-<version>.zip          install-from-zip package / release asset
  repository.traktstyle-<version>.zip    repository add-on package / release asset
  site/                                  GitHub Pages content (gh-pages branch)
"""
import hashlib
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SITE = DIST / "site"

SKIN_ID = "skin.traktstyle"
REPO_ID = "repository.traktstyle"
REPO_SRC = ROOT / "repository" / REPO_ID

# Repo-only files that must not end up inside the skin package.
SKIN_EXCLUDE = {".git", ".gitignore", ".gitattributes", "README.md", "build.py",
                "repository", "dist", "docs", "__pycache__"}


def addon_version(addon_xml: Path) -> str:
    text = addon_xml.read_text(encoding="utf-8")
    m = re.search(r'<addon\b[^>]*\bversion="([^"]+)"', text)
    return m.group(1)


def zip_addon(src: Path, addon_id: str, out: Path, exclude=frozenset()):
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.rglob("*")):
            rel = path.relative_to(src)
            if rel.parts[0] in exclude or not path.is_file():
                continue
            zf.write(path, f"{addon_id}/{rel.as_posix()}")
    return out


def addon_entry(addon_xml: Path) -> str:
    text = addon_xml.read_text(encoding="utf-8")
    return re.sub(r"^<\?xml[^>]*\?>\s*", "", text).strip()


def main():
    shutil.rmtree(DIST, ignore_errors=True)
    skin_ver = addon_version(ROOT / "addon.xml")
    repo_ver = addon_version(REPO_SRC / "addon.xml")

    skin_zip = zip_addon(ROOT, SKIN_ID, DIST / f"{SKIN_ID}-{skin_ver}.zip", SKIN_EXCLUDE)
    repo_zip = zip_addon(REPO_SRC, REPO_ID, DIST / f"{REPO_ID}-{repo_ver}.zip")

    # Kodi repository layout: <datadir>/<id>/<id>-<version>.zip + artwork.
    for addon_id, zf, art_dir in ((SKIN_ID, skin_zip, ROOT / "resources"),
                                  (REPO_ID, repo_zip, REPO_SRC)):
        d = SITE / addon_id
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(zf, d / zf.name)
        for art in ("icon.png", "fanart.jpg"):
            if (art_dir / art).exists():
                shutil.copy2(art_dir / art, d / art)

    # Stable, version-less name for the Downloader app / browser links.
    shutil.copy2(repo_zip, SITE / f"{REPO_ID}.zip")
    shutil.copy2(skin_zip, SITE / f"{SKIN_ID}.zip")

    addons_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
                  + addon_entry(ROOT / "addon.xml") + "\n"
                  + addon_entry(REPO_SRC / "addon.xml") + "\n</addons>\n")
    (SITE / "addons.xml").write_text(addons_xml, encoding="utf-8", newline="\n")
    (SITE / "addons.xml.md5").write_text(
        hashlib.md5(addons_xml.encode("utf-8")).hexdigest(), encoding="utf-8")

    # Kodi browses an http:// source by reading the <a href> links of the page.
    (SITE / "index.html").write_text(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Trakt Style for Kodi</title></head>
<body style="font-family:sans-serif;background:#16141c;color:#eee;padding:24px">
<h1>Trakt Style for Kodi</h1>
<p>Add this page as a file source in Kodi, then <i>Install from zip file</i> &rarr; pick the repository zip.</p>
<ul>
<li><a href="{REPO_ID}.zip">{REPO_ID}.zip</a> (repository &ndash; recommended, gets updates)</li>
<li><a href="{SKIN_ID}.zip">{SKIN_ID}.zip</a> (skin {skin_ver} only, no auto-updates)</li>
</ul>
<p><a href="https://github.com/sedvis/kodi-trakt-style-theme">github.com/sedvis/kodi-trakt-style-theme</a></p>
</body></html>
""", encoding="utf-8", newline="\n")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    print(f"skin {skin_ver}: {skin_zip}")
    print(f"repo {repo_ver}: {repo_zip}")
    print(f"site: {SITE}")


if __name__ == "__main__":
    main()
