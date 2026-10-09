"""Generate xml/Home.xml (the skin lives at the repository root).

The home screen mirrors the Trakt web app: a Media / Shows / Movies switcher at the top, a floating
icon rail on the left, and horizontal rows fed by Elementum's Trakt routes. Edit ROWS to change them.
"""
import os

SKIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
E = "plugin://plugin.video.elementum"

# (list_id, mode, kind, label, path, flags)
#   kind: poster | landscape | calendar      flags: auth (needs Trakt sign-in), library (needs local library)
#   flag play: selecting an item plays it right away (default: open the info page first)
ROWS = [
    # ---- Media (mixed, like Trakt's home)
    (5101, "media", "landscape", "Continue Watching", f"{E}/shows/trakt/progress", {"auth", "play"}),
    (5102, "media", "calendar", "Calendar", f"{E}/shows/trakt/calendars/shows", {"auth"}),
    (5103, "media", "poster", "Watchlist · Movies", f"{E}/movies/trakt/watchlist", {"auth"}),
    (5104, "media", "poster", "Watchlist · Shows", f"{E}/shows/trakt/watchlist", {"auth"}),
    (5105, "media", "poster", "Recommended Movies", f"{E}/movies/trakt/recommendations", {"auth"}),
    (5106, "media", "poster", "Trending Movies", f"{E}/movies/trakt/trending", set()),
    (5107, "media", "poster", "Trending Shows", f"{E}/shows/trakt/trending", set()),
    (5108, "media", "poster", "In Progress · Library", "special://skin/playlists/inprogress_movies.xsp", {"library_movies"}),
    (5109, "media", "landscape", "Recently Added Episodes · Library", "videodb://recentlyaddedepisodes/", {"library_tv"}),
    # ---- Shows
    (5201, "shows", "landscape", "Continue Watching", f"{E}/shows/trakt/progress", {"auth", "play"}),
    (5202, "shows", "calendar", "Calendar", f"{E}/shows/trakt/calendars/shows", {"auth"}),
    (5203, "shows", "poster", "Trending", f"{E}/shows/trakt/trending", set()),
    (5204, "shows", "poster", "Popular", f"{E}/shows/trakt/popular", set()),
    (5205, "shows", "poster", "Anticipated", f"{E}/shows/trakt/anticipated", set()),
    (5206, "shows", "poster", "Recommended", f"{E}/shows/trakt/recommendations", {"auth"}),
    (5207, "shows", "poster", "Watchlist", f"{E}/shows/trakt/watchlist", {"auth"}),
    (5208, "shows", "calendar", "Premieres", f"{E}/shows/trakt/calendars/allpremieres", set()),
    (5209, "shows", "poster", "TV Shows · Library", "videodb://tvshows/titles/", {"library_tv"}),
    # ---- Movies
    (5301, "movies", "poster", "Trending", f"{E}/movies/trakt/trending", set()),
    (5302, "movies", "landscape", "Box Office", f"{E}/movies/trakt/boxoffice", set()),
    (5303, "movies", "poster", "Anticipated", f"{E}/movies/trakt/anticipated", set()),
    (5304, "movies", "poster", "Popular", f"{E}/movies/trakt/popular", set()),
    (5305, "movies", "poster", "Recommended", f"{E}/movies/trakt/recommendations", {"auth"}),
    (5306, "movies", "poster", "Watchlist", f"{E}/movies/trakt/watchlist", {"auth"}),
    (5307, "movies", "poster", "Top Rated", f"{E}/movies/top", set()),
    (5308, "movies", "poster", "Movies · Library", "videodb://movies/titles/", {"library_movies"}),
]

ICONS = {"Continue Watching": "trakt/icons/section.png"}

MODE_EXP = {"media": "$EXP[home_mode_media]", "shows": "$EXP[home_mode_shows]", "movies": "$EXP[home_mode_movies]"}


def row_condition(mode, path, flags):
    cond = [MODE_EXP[mode]]
    if path.startswith(E):
        cond.append("$EXP[elementum_on]")
    if "auth" in flags:
        cond.append("$EXP[trakt_signed_in]")
    if "library_movies" in flags:
        cond.append("Library.HasContent(movies) + !Skin.HasSetting(home_no_library)")
    if "library_tv" in flags:
        cond.append("Library.HasContent(tvshows) + !Skin.HasSetting(home_no_library)")
    return " + ".join(cond)


def row_path_variable(list_id, mode, kind, label, path, flags):
    """The row's content path, empty while the row is not shown. Kodi's directory provider does
    not fetch an empty path, so only the rows of the active tab (and the personal rows only when
    Trakt is connected) call Elementum, instead of every row of every tab at once."""
    path_xml = path.replace("&", "&amp;")
    return (
        f'\t<variable name="TraktRowPath_{list_id}">\n'
        f'\t\t<value condition="{row_condition(mode, path, flags)}">{path_xml}</value>\n'
        f"\t</variable>\n"
    )


def row_xml(list_id, mode, kind, label, path, flags):
    visible = row_condition(mode, path, flags)
    inc = {"poster": "TraktPosterRow", "landscape": "TraktLandscapeRow", "calendar": "TraktLandscapeRow"}[kind]
    extra = ""
    if kind == "calendar":
        extra = (
            '\t\t\t\t\t\t<param name="pill_right">$INFO[ListItem.Premiered]</param>\n'
            '\t\t\t\t\t\t<param name="pill_right_visible">true</param>\n'
        )
    if "play" in flags:
        extra += '\t\t\t\t\t\t<param name="open_info">false</param>\n'
    return (
        f'\t\t\t\t\t<include content="{inc}">\n'
        f'\t\t\t\t\t\t<param name="list_id">{list_id}</param>\n'
        f'\t\t\t\t\t\t<param name="label">{label}</param>\n'
        f'\t\t\t\t\t\t<param name="path">$VAR[TraktRowPath_{list_id}]</param>\n'
        f'\t\t\t\t\t\t<param name="visible">{visible}</param>\n'
        f"{extra}"
        f"\t\t\t\t\t</include>\n"
    )


def nav_tab(btn_id, left, mode, label, icon, onleft, onright):
    active = MODE_EXP[mode]
    return f"""			<control type="group">
				<left>{left}</left>
				<top>6</top>
				<width>176</width>
				<height>48</height>
				<control type="image">
					<texture colordiffuse="accent" border="24">trakt/frames/pill48.png</texture>
					<visible>{active}</visible>
				</control>
				<control type="button" id="{btn_id}">
					<texturefocus colordiffuse="text_hi" border="24">trakt/frames/pill48-ring.png</texturefocus>
					<texturenofocus />
					<label></label>
					<onclick>Skin.SetString(home_mode,{mode})</onclick>
					<!-- Rows of the new tab are hidden and so never re-read their (now non-empty) content
					     path; show them for a moment so they start loading (see the Rows notes in Includes_Trakt.xml). -->
					<onclick>SetProperty(trakt_rows_kick,1,home)</onclick>
					<onclick>AlarmClock(trakt_rows_kick,ClearProperty(trakt_rows_kick,home),00:01,silent)</onclick>
					<onleft>{onleft}</onleft>
					<onright>{onright}</onright>
					<onup>noop</onup>
					<ondown>5000</ondown>
				</control>
				<control type="image">
					<left>26</left>
					<top>11</top>
					<width>26</width>
					<height>26</height>
					<texture colordiffuse="text_hi">trakt/icons/{icon}.png</texture>
					<visible>{active} | Control.HasFocus({btn_id})</visible>
				</control>
				<control type="image">
					<left>26</left>
					<top>11</top>
					<width>26</width>
					<height>26</height>
					<texture colordiffuse="text_lo">trakt/icons/{icon}.png</texture>
					<visible>!{active} + !Control.HasFocus({btn_id})</visible>
				</control>
				<control type="label">
					<left>62</left>
					<width>110</width>
					<aligny>center</aligny>
					<font>t_nav</font>
					<textcolor>text_hi</textcolor>
					<label>{label}</label>
					<visible>{active} | Control.HasFocus({btn_id})</visible>
				</control>
				<control type="label">
					<left>62</left>
					<width>110</width>
					<aligny>center</aligny>
					<font>t_nav</font>
					<textcolor>text_lo</textcolor>
					<label>{label}</label>
					<visible>!{active} + !Control.HasFocus({btn_id})</visible>
				</control>
			</control>
"""


def rail_item(btn_id, icon, label, onclick, current="false", up_id="noop", down_id="noop"):
    clicks = "".join(f"\t\t\t\t\t<onclick>{c}</onclick>\n" for c in onclick)
    return f"""				<control type="group">
					<width>360</width>
					<height>72</height>
					<control type="button" id="{btn_id}">
						<left>6</left>
						<top>4</top>
						<width>64</width>
						<height>64</height>
						<texturefocus colordiffuse="accent" border="18">trakt/frames/rr16.png</texturefocus>
						<texturenofocus />
						<label></label>
{clicks}						<onup>{up_id}</onup>
						<ondown>{down_id}</ondown>
						<onleft>noop</onleft>
						<onright>5000</onright>
					</control>
					<control type="image">
						<left>21</left>
						<top>19</top>
						<width>34</width>
						<height>34</height>
						<texture colordiffuse="text_hi">trakt/icons/{icon}.png</texture>
						<visible>Control.HasFocus({btn_id}) | !({current})</visible>
					</control>
					<control type="image">
						<left>21</left>
						<top>19</top>
						<width>34</width>
						<height>34</height>
						<texture colordiffuse="accent_light">trakt/icons/{icon}.png</texture>
						<visible>!Control.HasFocus({btn_id}) + {current}</visible>
					</control>
					<control type="group">
						<left>96</left>
						<top>14</top>
						<visible>Control.HasFocus({btn_id})</visible>
						<animation effect="fade" time="150">Visible</animation>
						<animation effect="slide" start="-10,0" end="0,0" time="150">Visible</animation>
						<control type="image">
							<width>210</width>
							<height>44</height>
							<texture colordiffuse="surface_hi" border="22">trakt/frames/pill44.png</texture>
						</control>
						<control type="label">
							<left>20</left>
							<width>180</width>
							<height>44</height>
							<aligny>center</aligny>
							<font>t_label</font>
							<textcolor>text_hi</textcolor>
							<label>{label}</label>
						</control>
					</control>
				</control>
"""


def build():
    rows = "".join(row_xml(*r) for r in ROWS)
    rail = "".join([
        rail_item(9001, "search", "Search", ["ActivateWindow(1107)"], up_id="101", down_id="9002"),
        rail_item(9002, "home", "Home", ["SetFocus(5000)"], current="true", up_id="9001", down_id="9003"),
        rail_item(9003, "discover", "Discover", [f"ActivateWindow(Videos,{E}/,return)"], up_id="9002", down_id="9004"),
        rail_item(9004, "lists", "Lists", [
            ("$EXP[home_mode_shows]", f"ActivateWindow(Videos,{E}/shows/trakt/lists/,return)"),
            ("!$EXP[home_mode_shows]", f"ActivateWindow(Videos,{E}/movies/trakt/lists/,return)"),
        ], up_id="9003", down_id="9005"),
        rail_item(9005, "library", "Library", ["ActivateWindow(Videos,library://video/,return)"], up_id="9004", down_id="9006"),
        rail_item(9006, "addons", "Add-ons", ["ActivateWindow(Videos,addons://sources/video/,return)"], up_id="9005", down_id="9007"),
        rail_item(9007, "settings", "Settings", ["ActivateWindow(Settings)"], up_id="9006", down_id="9010"),
    ])
    tabs = (
        nav_tab(101, 6, "media", "Media", "media", 9000, 102)
        + nav_tab(102, 188, "shows", "Shows", "shows", 101, 103)
        + nav_tab(103, 370, "movies", "Movies", "movies", 102, "noop")
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATED by tools/build_home.py - edit the generator, not this file. -->
<window>
	<defaultcontrol always="true">5000</defaultcontrol>
	<backgroundcolor>background</backgroundcolor>
	<!-- Start-up jump into Elementum (set by Startup.xml); opened from here so Back returns to Home. -->
	<onload condition="String.IsEqual(Window(home).Property(trakt_autostart),1) + String.IsEqual(Skin.String(startup_target),elementum)">ActivateWindow(Videos,"plugin://plugin.video.elementum/",return)</onload>
	<onload condition="String.IsEqual(Window(home).Property(trakt_autostart),1) + String.IsEqual(Skin.String(startup_target),movies)">ActivateWindow(Videos,"plugin://plugin.video.elementum/movies/",return)</onload>
	<onload condition="String.IsEqual(Window(home).Property(trakt_autostart),1) + String.IsEqual(Skin.String(startup_target),shows)">ActivateWindow(Videos,"plugin://plugin.video.elementum/shows/",return)</onload>
	<onload>ClearProperty(trakt_autostart,home)</onload>
	<onload condition="String.IsEmpty(Window(home).Property(trakt_wheel_synced))">RunScript(special://skin/scripts/home_wheel.py)</onload>
	<!-- Show the skin version once after it changes (repository update or first install). -->
	<onload condition="String.IsEmpty(Skin.String(seen_version))">Notification(Trakt Style,Version $INFO[System.AddonVersion(skin.traktstyle)] installed,6000,special://skin/resources/icon.png)</onload>
	<onload condition="!String.IsEmpty(Skin.String(seen_version)) + !String.IsEqual(Skin.String(seen_version),System.AddonVersion(skin.traktstyle))">Notification(Trakt Style,Updated to version $INFO[System.AddonVersion(skin.traktstyle)],6000,special://skin/resources/icon.png)</onload>
	<onload condition="!String.IsEqual(Skin.String(seen_version),System.AddonVersion(skin.traktstyle))">Skin.SetString(seen_version,$INFO[System.AddonVersion(skin.traktstyle)])</onload>
	<controls>
		<include>TraktBackground</include>
		<control type="videowindow">
			<depth>DepthBackground</depth>
			<include>FullScreenDimensions</include>
			<visible>Player.HasVideo + !Slideshow.IsActive</visible>
		</control>
		<!-- Backdrop of the focused card, faded into the ink like Trakt's hero cards -->
		<control type="group">
			<depth>DepthBackground</depth>
			<visible>Skin.HasSetting(home_backdrop) + !Player.HasVideo</visible>
			<animation effect="fade" start="0" end="100" time="400">WindowOpen</animation>
			<animation effect="fade" start="100" end="0" time="250">WindowClose</animation>
			<control type="image">
				<left>620</left>
				<top>0</top>
				<width>1300</width>
				<height>732</height>
				<aspectratio>scale</aspectratio>
				<fadetime>500</fadetime>
				<texture background="true" colordiffuse="60FFFFFF">$VAR[HomeBackdropVar]</texture>
			</control>
			<control type="image">
				<left>620</left>
				<top>0</top>
				<width>760</width>
				<height>732</height>
				<texture colordiffuse="ink">trakt/gradients/left.png</texture>
			</control>
			<control type="image">
				<left>620</left>
				<top>300</top>
				<width>1300</width>
				<height>432</height>
				<texture colordiffuse="ink">trakt/gradients/bottom.png</texture>
			</control>
			<control type="image">
				<left>620</left>
				<top>0</top>
				<width>1300</width>
				<height>150</height>
				<texture colordiffuse="99000000">trakt/gradients/top.png</texture>
			</control>
		</control>

		<!-- ================================================================ Content rows -->
		<control type="grouplist" id="5000">
			<left>138</left>
			<top>104</top>
			<width>1782</width>
			<bottom>0</bottom>
			<orientation>vertical</orientation>
			<itemgap>6</itemgap>
			<scrolltime tween="cubic" easing="out">420</scrolltime>
			<onup condition="$EXP[home_mode_media]">101</onup>
			<onup condition="$EXP[home_mode_shows]">102</onup>
			<onup condition="$EXP[home_mode_movies]">103</onup>
			<!-- Without this the grouplist wraps Down from the last row to the first one. -->
			<ondown>noop</ondown>
			<onleft>9000</onleft>
			<usecontrolcoords>true</usecontrolcoords>
			<animation effect="fade" start="100" end="45" time="200" condition="ControlGroup(9000).HasFocus | Control.HasFocus(9010)">Conditional</animation>
			<animation effect="fade" start="0" end="100" time="350">WindowOpen</animation>
			<include content="TraktHomeNotice">
				<param name="id">5091</param>
				<param name="title">Connect Trakt in Elementum</param>
				<param name="text">Sign in to Trakt in Elementum's settings and your Continue Watching, Calendar and Watchlist rows will appear here.</param>
				<param name="button">Open Elementum settings</param>
				<param name="onclick">Addon.OpenSettings(plugin.video.elementum)</param>
				<param name="visible">$EXP[elementum_on] + String.IsEmpty(Addon.SettingStr(plugin.video.elementum,trakt_token)) + !$EXP[home_mode_movies]</param>
			</include>
			<include content="TraktHomeNotice">
				<param name="id">5092</param>
				<param name="title">Elementum isn't enabled</param>
				<param name="text">The Trakt rows on this screen come from the Elementum add-on. Install or enable it, then come back.</param>
				<param name="button">Open add-ons</param>
				<param name="onclick">ActivateWindow(AddonBrowser)</param>
				<param name="visible">!$EXP[elementum_on]</param>
			</include>
{rows}		</control>

		<!-- ================================================================ Top bar -->
		<control type="image">
			<left>0</left>
			<top>0</top>
			<width>1920</width>
			<height>130</height>
			<texture colordiffuse="ink">trakt/gradients/top.png</texture>
		</control>
		<control type="group" id="100">
			<left>681</left>
			<top>20</top>
			<width>558</width>
			<height>60</height>
			<control type="image">
				<texture colordiffuse="ink_deep" border="28">trakt/frames/pill56.png</texture>
			</control>
{tabs}		</control>
		<control type="grouplist">
			<right>40</right>
			<top>24</top>
			<width>700</width>
			<height>52</height>
			<orientation>horizontal</orientation>
			<align>right</align>
			<itemgap>26</itemgap>
			<usecontrolcoords>true</usecontrolcoords>
			<control type="group">
				<width>270</width>
				<visible>$EXP[elementum_on]</visible>
				<control type="image">
					<texture colordiffuse="accent" border="24">trakt/frames/pill48-ring.png</texture>
					<height>52</height>
				</control>
				<control type="image">
					<left>8</left>
					<top>8</top>
					<width>36</width>
					<height>36</height>
					<texture colordiffuse="accent">trakt/frames/circle.png</texture>
				</control>
				<control type="image">
					<left>16</left>
					<top>16</top>
					<width>20</width>
					<height>20</height>
					<texture colordiffuse="text_hi">trakt/icons/user.png</texture>
				</control>
				<control type="label">
					<left>56</left>
					<right>20</right>
					<height>52</height>
					<aligny>center</aligny>
					<font>t_label_b</font>
					<textcolor>text_hi</textcolor>
					<label>$VAR[TraktUserLabel]</label>
				</control>
			</control>
			<control type="label">
				<width>auto</width>
				<height>52</height>
				<aligny>center</aligny>
				<font>t_clock</font>
				<textcolor>text_hi</textcolor>
				<label>$INFO[System.Time]</label>
			</control>
		</control>

		<!-- ================================================================ Left rail -->
		<control type="image">
			<left>26</left>
			<top>262</top>
			<width>84</width>
			<height>524</height>
			<texture colordiffuse="ink_deep" border="26">trakt/frames/rr24.png</texture>
		</control>
		<control type="grouplist" id="9000">
			<left>30</left>
			<top>270</top>
			<width>400</width>
			<height>520</height>
			<orientation>vertical</orientation>
			<itemgap>0</itemgap>
			<onright>5000</onright>
			<onup>101</onup>
			<ondown>9010</ondown>
			<onleft>noop</onleft>
			<defaultcontrol>9002</defaultcontrol>
{rail}		</control>
		<control type="group">
			<left>36</left>
			<bottom>36</bottom>
			<width>64</width>
			<height>64</height>
			<control type="button" id="9010">
				<texturefocus colordiffuse="accent">trakt/frames/circle.png</texturefocus>
				<texturenofocus colordiffuse="surface">trakt/frames/circle.png</texturenofocus>
				<label></label>
				<onclick>ActivateWindow(ShutdownMenu)</onclick>
				<onup>9007</onup>
				<ondown>noop</ondown>
				<onleft>noop</onleft>
				<onright>5000</onright>
			</control>
			<control type="image">
				<left>16</left>
				<top>16</top>
				<width>32</width>
				<height>32</height>
				<texture colordiffuse="text_hi">trakt/icons/power.png</texture>
			</control>
		</control>
	</controls>
</window>
"""
    with open(os.path.join(SKIN, "xml", "Home.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(xml)
    variables = "".join(row_path_variable(*r) for r in ROWS)
    with open(os.path.join(SKIN, "xml", "Includes_HomeRows.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                "<!-- GENERATED by tools/build_home.py - edit the generator, not this file. -->\n"
                f"<includes>\n{variables}</includes>\n")
    print("Home.xml written:", len(ROWS), "rows")


if __name__ == "__main__":
    build()
