# -*- coding: utf-8 -*-
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
#------------------------------------------------------------

import os
import sys
import plugintools
import xbmc,xbmcaddon
import httplib
from urlparse import urljoin,urlparse
from HTMLParser import HTMLParser
import re



addonID = 'plugin.video.mazedabd'
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')
fanart = local.getAddonInfo('fanart')

MAIN_IP = "172.22.22.101"

videoFormats = ["mp4", "mkv", "avi", "mpeg"]
posterFormats = ["jpg", "jpeg", "png"]
subtitleFormats = ["srt"]

ignoredFiles = ["WWW.YTS.AG.jpg"]

# Entry point
def run():
    plugintools.log("mazedabd.run")
    
    # Get params
    params = plugintools.get_params()
    
    if params.get("action") is None:
        fetch_main_items(params)
    elif params.get("action") == "explore":
        explore(params)
    elif params.get("action") == "play":
        play(params)
    
    plugintools.close_item_list()

def fetch_main_items(params):
    plugintools.add_item(
        action='explore',
        title="Latest",
        url="http://" + MAIN_IP + "/s1d4/Hasan/index.php",
        thumbnail=icon,
        fanart=fanart,
        folder=True
    )

    plugintools.log("fetching main items " + repr(params))
    resp = plugintools.read("http://" + MAIN_IP)
    regex = r"<a \s*href=\"list_files.php\?link=([^&]+)[^\"]*\"\s*>\s*([^<]+)<"

    matches = plugintools.find_multiple_matches(resp, regex)

    for item in matches:
        plugintools.add_item(
            action='explore',
            title=item[1],
            url=fixurl(item[0]),
            thumbnail=icon,
            fanart=fanart,
            folder=True
        )


def fixurl(url):
    if not url.startswith('http'):
        url = 'http://' + url

    return url

def explore(params):
    url = fixurl(params.get('url'))

    plugintools.log("Explore current url: " + url)
    resp = plugintools.read(url)
    regex = r"<tr[^>]+><td[^>]+><a .*?href=\"(?P<url>[^\"]+)\"><img.*?alt=\"\[(?P<type>[^\"]+)\]\"[^>]*?src=\"[^\"]+\"[^>]+>\s+(?P<title>.+?)<\/a>(?:\s?<img[^>]+>)?"

    matches = [m for m in re.findall(regex,resp) if m[2] not in ignoredFiles]
    h = HTMLParser()

    stats = getDirStats(matches)
    posterUrl = getFinalUrl(urljoin(url, h.unescape(stats[1]))) if stats[0] else ""
    subtitleUrl = getFinalUrl(urljoin(url, h.unescape(stats[2]))) if stats[0] else ""

    plugintools.log("Stats: " + str(stats[0]) + ", " + stats[1] + ", " + stats[2] + " Poster URL:" + posterUrl + " Subtitle URL:" + subtitleUrl)


    for item in matches:
        u = urljoin(url, h.unescape(item[0]))
        if item[1] == "dir":
            plugintools.add_item(
                action='explore',
                title= item[2],
                url=u,
                thumbnail=icon,
                fanart=fanart,
                folder= True
            )
        elif item[1] in videoFormats:
            plugintools.add_item(
                action='play',
                title=item[2],
                url=u,
                thumbnail=posterUrl,
                fanart=fanart,
                extra=subtitleUrl,
                isPlayable=True,
                folder=False
            )
        else:
            if stats[0] and (item[0] == stats[1] or item[0] == stats[2]):
                continue

            plugintools.add_item(
                title=item[2],
                url=u,
                thumbnail=getFinalUrl(u) if stats[0] and item[1] in posterFormats else "",
                isPlayable=False,
                folder=False
            )

def getDirStats(matches):

    videoCount = 0;

    subtitleFile = "";
    posterFile = "";

    for item in matches:
        if item[1] in videoFormats:
            videoCount = videoCount+1
        elif item[1] in posterFormats:
            posterFile = item[0]
        elif item[1] in subtitleFormats:
            subtitleFile = item[0]

    return (videoCount < 4, posterFile, subtitleFile)

def getFinalUrl(url):
    "Navigates Through redirections to get final url."
    parsed = urlparse(url)
    plugintools.log("Getting final url of: "+url)
    conn = httplib.HTTPConnection(parsed.netloc)
    conn.request("HEAD",parsed.path + "?" + parsed.query)
    response = conn.getresponse()
    if str(response.status).startswith("3"):
        new_location = [v for k,v in response.getheaders() if k == "location"][0]
        new_location = urljoin(url, new_location)
        return getFinalUrl(new_location)
    return url

def play(params):
    url = params.get('url')
    url = getFinalUrl(url)
    subtitle = params.get('extra')
    plugintools.log("play.run: " + url + " SUBTITLE: " + subtitle)



    plugintools.play_resolved_url(url)
    if subtitle:
        xbmc.Player().setSubtitles(subtitle)


run()