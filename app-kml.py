#!/usr/bin/env python
""" An app for serving IRLP coverage KML files.

:author: Ralph Bean <rbean@redhat.com>
"""

import uuid
import math

from fastkml import kml
from shapely.geometry import Polygon

import flask

app = flask.Flask(__name__)

def read_data(filename):
    with open(filename, 'r') as f:
        rows = [row.split('\t') for row in f.readlines()]

    headers, rows = rows[0], rows[1:]
    rows = [{
        headers[i]: row[i]
        for i in range(len(rows[0]))
    } for row in rows]
    return rows

# http://status.irlp.net/nohtmlstatus.txt.bz2
filename = 'nohtmlstatus.txt'

def circle_points(x0, y0, r, points=10):
    for i in range(points):
        theta = 2.0 * math.pi * ((i + 1) / float(points))
        x = (math.cos(theta) * r) + x0
        y = (math.sin(theta) * r) + y0
        yield (x, y)

@app.route('/')
def index():
    k = kml.KML()
    ns = '{http://www.opengis.net/kml/2.2}'
    d = kml.Document(ns, 'docid', 'doc name', 'doc description')
    f = kml.Folder(ns, 'fid', 'f name', 'f description')
    k.append(d)
    d.append(f)
    nf = kml.Folder(ns, 'nested-fid', 'nested f name', 'nested f description')
    f.append(nf)
    f2 = kml.Folder(ns, 'id2', 'name2', 'description2')
    d.append(f2)

    size = 1
    data = read_data(filename)
    for row in data:
        try:
            lon = float(row['long'])
            lat = float(row['lat'])
        except ValueError:
            #print "failed on %r" % row
            continue

        p = kml.Placemark(ns, 'id-' + str(uuid.uuid4()), 'name', 'description')
        p.geometry =  Polygon(list(circle_points(lon, lat, size, 10)))
        f2.append(p)

    data = k.to_string(prettyprint=True)
    response = flask.make_response(data)
    response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
    return response

if __name__ == '__main__':
    app.debug = True
    app.run(
        host='0.0.0.0',
    )
