import os
import sys
sys.path.append(os.path.dirname(__file__))

import json
import dateutil.parser
import re
import random
import requests
from time import sleep
from pymongo import MongoClient
from bson.objectid import ObjectId
from urlparse import urlparse
from copy import deepcopy

from flask import Flask, request, send_from_directory, safe_join, Response
from flask.ext.cors import CORS
from collections import Counter
app = Flask(__name__)
CORS(app)

MONGO_URL = os.environ['MONGOLAB_URI']
MONGO_CLIENT = MongoClient(MONGO_URL)
MONGO_DB = MONGO_CLIENT[urlparse(MONGO_URL).path[1:]]


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

def get_map(route):
    map_filename = os.path.join(os.path.dirname(__file__), 'map_cache/trip_'+route['route_id']+'.png')
    if not os.path.exists(map_filename):
        start_pos = route['legs'][0]['start']
        finish_pos = route['legs'][-1]['end']
        map_url = 'https://maps.googleapis.com/maps/api/staticmap'
        map_params = {'size': '330x350',
                      'markers': [ 'color:red|'+coord_to_str(start_pos), 'color:green|'+coord_to_str(finish_pos)],
                      'path': ['color:blue|'+coord_to_str(leg['start'])+'|'+coord_to_str(leg['end']) for leg in route['legs']],
                      }
        resp = requests.get(map_url, map_params)
        if resp.status_code == 200:
            with open(map_filename, 'wb') as w:
                w.write(resp.content)
        print resp.status_code, map_url
        sleep(1)        
    with open(map_filename) as r:
        return r.read()
    
ROUTES_DB = jload(os.path.join(os.path.dirname(__file__), 'routes_2015-08-31_23_BRT.json'))
for i, route in enumerate(ROUTES_DB):
    route['route_id'] = str(i)
    get_map(route)
ROUTES_DB = dict([(str(t['route_id']), t) for t in ROUTES_DB])




@app.route("/api/users/<user_id>/feed", methods=['GET'])
def feed(user_id):
    feed_items = []

    trips = [trip for trip in MONGO_DB.trips.find({'user_id': user_id}) if trip['route_id'] in ROUTES_DB]
    if len(trips) == 0:
        for route in random.sample(ROUTES_DB.values(), 10):
            trip = deepcopy(route)
            trip['user_id'] = user_id
            trips.append(trip)
        MONGO_DB.trips.insert_many(trips)
        trips = [trip for trip in MONGO_DB.trips.find({'user_id': user_id}) if trip['route_id'] in ROUTES_DB]
    for trip in trips:
        trip['trip_id'] = str(trip['_id'])
        del trip['_id']
        feed_items.append({'item_type': 'my_trip',
                           'item_id': trip['trip_id'],
                           'item_details': trip,
                           })
    return Response(json.dumps(feed_items), mimetype='application/json')
    
@app.route("/api/trips/<trip_id>", methods=['GET'])
def trips(trip_id):
    trip = MONGO_DB.trips.find_one({'_id': ObjectId(trip_id)})
    trip['trip_id'] = str(trip['_id'])
    del trip['_id']
    return Response(json.dumps(trip), mimetype='application/json')


@app.route("/api/trips/<trip_id>/map", methods=['GET'])
def trip_map(trip_id):
    trip = MONGO_DB.trips.find_one({'_id': ObjectId(trip_id)})
    return Response(get_map(ROUTES_DB[trip['route_id']]), mimetype='image/png')

@app.route("/api/users/<user_id>/routes", methods=['GET'])
def user_routes(user_id):
    route_ids = Counter([trip['route_id'] for trip in MONGO_DB.trips.find({'user_id': user_id}) if trip['route_id'] in ROUTES_DB])
    routes = [deepcopy(ROUTES_DB[route_id]) for route_id in route_ids.keys()]
    routes.sort(key=lambda route: route_ids[route['route_id']])
    routes.reverse()
    routes = routes[:5]
    return Response(json.dumps(routes), mimetype='application/json')
    
        
    
    
    
    




    
if __name__ == "__main__":
    app.run('0.0.0.0', 3000, debug=True)
