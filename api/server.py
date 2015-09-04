import os
import sys
sys.path.append(os.path.dirname(__file__))

import json
import dateutil.parser
import re
import random
import requests
from time import sleep

from flask import Flask, request, send_from_directory, safe_join, Response
from flask.ext.cors import CORS
app = Flask(__name__)
CORS(app)


def dump(filename, content):
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(filename, 'w') as w:
        w.write(content)

def load(filename):
    with open(filename, 'r') as r:
        return r.read()
        
def jdump(jval, filename):
    jdir = os.path.dirname(filename)
    if jdir and not os.path.exists(jdir):
        os.makedirs(jdir)
    with open(filename, 'w') as w:
        json.dump(jval, w, indent=2)

def jload(filename):
    with open(filename, 'r') as r:
        return json.load(r)        



@app.route("/api/test")
def sample():
    resp = {"Testing": "Hello world!"}
    return Response(json.dumps(resp), mimetype='application/json')

@app.route("/api/test/echo/<arg>", methods=['GET', 'PUT', 'DELETE', 'POST'])
def sample_echo(arg):
    if request.method in ['POST','PUT']:
        req = json.loads(request.get_data())
    else:
        req = {}
    resp = {"Testing Arg": arg,
            "Testing Method": request.method,
            "Testing Data": req}
    return Response(json.dumps(resp), mimetype='application/json')

def coord_to_str(coord):
    if type(coord) == list or type(coord) == tuple:
        return str(coord[0])+','+str(coord[1])
    else:
        return str(coord['latitude'])+','+str(coord['longitude'])

def get_map(trip):
    map_filename = os.path.join(os.path.dirname(__file__), 'map_cache/trip_'+trip['trip_id']+'.png')
    if not os.path.exists(map_filename):
        start_pos = trip['legs'][0]['start']
        finish_pos = trip['legs'][-1]['end']
        map_url = 'https://maps.googleapis.com/maps/api/staticmap'
        map_params = {'size': '330x350',
                      'markers': [ 'color:red|'+coord_to_str(start_pos), 'color:green|'+coord_to_str(finish_pos)],
                      'path': ['color:blue|'+coord_to_str(leg['start'])+'|'+coord_to_str(leg['end']) for leg in trip['legs']],
                      }
        resp = requests.get(map_url, map_params)
        if resp.status_code == 200:
            with open(map_filename, 'wb') as w:
                w.write(resp.content)
        print resp.status_code, map_url
        sleep(1)        
    with open(map_filename) as r:
        return r.read()
    
TRIPS_DB = jload(os.path.join(os.path.dirname(__file__), 'routes_2015-08-31_23_BRT.json'))
for i, t in enumerate(TRIPS_DB):
    t['trip_id'] = str(i)
    get_map(t)
TRIPS_DB = dict([(str(t['trip_id']), t) for t in TRIPS_DB])



@app.route("/api/users/<user_id>/feed", methods=['GET'])
def feed(user_id):
    feed_items = []
    for trip in random.sample(TRIPS_DB.values(), 10):
        feed_items.append({'item_type': 'my_trip',
                           'item_id': trip['trip_id'],
                           'item_details': trip,
                           })
    return Response(json.dumps(feed_items), mimetype='application/json')
    
@app.route("/api/trips/<trip_id>", methods=['GET'])
def trips(trip_id):
    return Response(json.dumps(TRIPS_DB[trip_id]), mimetype='application/json')



@app.route("/api/trips/<trip_id>/map", methods=['GET'])
def trip_map(trip_id):
    trip = TRIPS_DB[trip_id]
    return Response(get_map(trip), mimetype='image/png')


    
if __name__ == "__main__":
    app.run('0.0.0.0', 3000, debug=True)
