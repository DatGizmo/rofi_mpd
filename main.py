import datetime
import json
import os
import stat
import sys
import time
from collections import OrderedDict

from rofi import Rofi
from mpd import MPDClient


def get_album_release_epoch(x):
    song_data = x[1][0]
    if 'date' not in song_data:
        return -99999999999
    else:
        date = song_data['date']
        if '-' not in date:
            year = int(date)
            epoch = datetime.datetime(year, 1, 1)
        else:
            year, month, day = date.split('-')
            epoch = datetime.datetime(int(year), int(month), int(day))

        return int(epoch.timestamp())


client = MPDClient()
client.connect('localhost', 6600)

if os.path.isfile('database.json'):
    reload = time.time() - os.stat('database.json')[stat.ST_MTIME] > 600
else:
    reload = True

if reload:
    library_dict = {}

    library = client.listallinfo()
    for song in library:
        if 'artist' in song:
            artist = song['artist']
            if artist not in library_dict:
                library_dict[artist] = {}

            album = song['album']
            if album not in library_dict[artist]:
                library_dict[artist][album] = []

            library_dict[artist][song['album']].append(song)

    with open('database.json', 'w') as f:
        f.write(json.dumps(library_dict))

else:
    with open('database.json', 'r') as f:
        library_dict = json.loads(f.read())

r = Rofi()
index, key = r.select('Search artists', library_dict.keys())
if key == -1:
    sys.exit()

artist = [*library_dict][index]
albums = OrderedDict(library_dict[artist])
albums = sorted(albums.items(), key=lambda x: get_album_release_epoch(x))


index, key = r.select('Search %s' % artist, [album[0] for album in albums])
if key == -1:
    sys.exit()

album = albums[index][0]

tracks = albums[index][1]
# tracks = OrderedDict(albums[index])
tracks = sorted(tracks, key=lambda x: (int(x['disc']), int(x['track'])))
tracks = ["All"] + tracks

index, key = r.select('Search %s' % album, ['%s.%s - %s' % (t['disc'] if 'disc' in t else '1', t['track'], t['title'])
                                            if isinstance(t, dict)
                                            else t for t in tracks])

if index == 0:
    for track in tracks[1:]:
        client.add(track['file'])
    sys.exit()

track = [*tracks][index]
client.add(track['file'])