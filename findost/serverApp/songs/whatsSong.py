#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'LexusLee'
from urllib import urlencode
import requests
import json
from tornado import gen
from foundation.log import logger

WHATS_SONG_URL = 'https://www.what-song.com/api/'
ALLOW_GROUP = ['tvshow', 'movie', 'artist', 'game']
SPOTIFY_TRACK_URL = 'https://open.spotify.com/track/'
OST_URL = {
    'tvshow': 'https://www.what-song.com/api/tv-info?tvshowID=',
    'movie': 'https://www.what-song.com/api/movie-info?movieID=',
    'artist': 'https://www.what-song.com/api/artise-info?artiseID=',
    'game': 'https://www.what-song.com/api/game-info?gameID='
}


class WhatsSongSpider(object):
    """
    该模块用于调用有道智云api
    """
    def __init__(self):
        pass

    def get_whatssong_info(self, series_name, group='tvshow', limit=20):
        # default search songs in tv series
        if group not in ALLOW_GROUP:
            raise Exception("Invalid search group type")
        param_dict = {
            'limit': limit,
            'type': group,
            'field': series_name
        }
        series_info_url = WHATS_SONG_URL + 'search?{search_input}'.format(search_input=urlencode(param_dict))
        r = requests.get(series_info_url)
        result = json.loads(r.content)['data'][0]['data']
        if result:
            return result
        else:
            return None

    def get_ost_albums(self, _id, group='tvshow'):
        # default search songs in tv series
        if group not in ALLOW_GROUP:
            raise Exception("Invalid search group type")
        ost_url = OST_URL[group] + str(_id)
        r = requests.get(ost_url)
        result = json.loads(r.content)['data']['albums']
        if result:
            return result
        else:
            return None

    def get_ost_songs(self, album):
        pass

    @gen.coroutine
    def get_result(self, q, src_lang, dst_lang):
        url = self.build_get_url(q, src_lang, dst_lang)
        r = requests.get(url)
        raise gen.Return(r.content)


wss = WhatsSongSpider()
print(wss.get_ost_albums(_id=196))