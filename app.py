import math
import uuid

import geojson
import flask
import tw2.polymaps
import yaml
import fastkml
import shapely.geometry

from tw2.polymaps.geojsonify import geojsonify
from tw2.core.middleware import make_middleware


app = flask.Flask(__name__)
app.wsgi_app = make_middleware(app.wsgi_app)

template = """
<html>
<head>
<style type="text/css">
svg {
        width: 100%;
        height: 100%;
}

.midnight-commander-extras {
        width: 100%;
        height: 100%;
}

.layer circle {
  fill: lawngreen;
  fill-opacity: .5;
  stroke: green;
  vector-effect: non-scaling-stroke;
}
</style>
</head>
<body>
{{map.display()}}
</body>
</html>
"""


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
data = read_data(filename)


@app.route('/polymap')
def polymap():
    return flask.templating.render_template_string(template, map=PolyMap)


class PolyMap(tw2.polymaps.PolyMap):
    id = 'polymap'
    data_url = '/controllers/polymap/'
    interact = True
    zoom = 2.1
    center_latlon = {'lat': 35.8, 'lon': -344.2}
    hash = True
    cloudmade_api_key = "1a1b06b230af4efdbb989ea99e9841af"
    cloudmade_tileset = 'midnight-commander'
    css_class = 'midnight-commander-extras'
    properties_callback = """function (_layer) {
        _layer.on("load", org.polymaps.stylist()
        .title(function(d) { return "Lon/lat:  " + d.properties.ATTR }));
        return _layer
    }"""

    @classmethod
    @geojsonify
    def request(cls, req):
        features = []
        for row in data:
            try:
                lon = float(row['long'])
                lat = float(row['lat'])
            except ValueError:
                print "failed on %r" % row
                continue
            feature = geojson.Feature(
                geometry=geojson.Point([lon, lat]),
                properties={'ATTR': "%s, %s" % (lon, lat)}
            )
            features.append(feature)

        return geojson.FeatureCollection(features=features)


def circle_points(x0, y0, r, points=10):
    for i in range(points):
        theta = 2.0 * math.pi * ((i + 1) / float(points))
        x = (math.cos(theta) * r) + x0
        y = (math.sin(theta) * r) + y0
        yield (x, y)


@app.route('/kml')
def kml():
    k = fastkml.kml.KML()
    ns = '{http://www.opengis.net/kml/2.2}'
    d = fastkml.kml.Document(
        ns, 'id', 'IRLP nodes',
        'IRLP nodes from http://status.irlp.net/nohtmlstatus.txt.bz2')
    f = fastkml.kml.Folder(ns, 'id', 'IRLP nodes', 'IRLP nodes')
    d.append(f)

    size = 1
    for row in data:
        try:
            lon = float(row['long'])
            lat = float(row['lat'])
        except ValueError:
            #print "failed on %r" % row
            continue

        p = fastkml.kml.Placemark(
            ns, 'id-' + str(uuid.uuid4()), row['CallSign'], yaml.dump(row))
        points = list(circle_points(lon, lat, size, 10))
        p.geometry = shapely.geometry.Polygon(points)
        f.append(p)

    body = k.to_string(prettyprint=True)
    response = flask.make_response(body)
    response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
    return response


if __name__ == '__main__':
    app.debug = True
    app.run()
