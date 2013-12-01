import random
import geojson
import flask
import tw2.polymaps

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


@app.route('/')
def index():
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


if __name__ == '__main__':
    app.debug = True
    app.run()
