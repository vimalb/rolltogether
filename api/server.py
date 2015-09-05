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

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']


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

def get_trip_map(trip):
    map_filename = os.path.join(os.path.dirname(__file__), 'map_cache/trip_'+trip['raw_trip_id']+'.png')
    if not os.path.exists(map_filename):
        start_pos = trip['legs'][0]['start']
        finish_pos = trip['legs'][-1]['end']
        map_url = 'https://maps.googleapis.com/maps/api/staticmap'
        map_params = {'size': '330x350',
                      'markers': [ 'color:red|'+coord_to_str(start_pos), 'color:green|'+coord_to_str(finish_pos)],
                      'path': ['color:blue|'+coord_to_str(leg['start'])+'|'+coord_to_str(leg['end']) for leg in trip['legs']],
                      'key': GOOGLE_API_KEY,
                      }
        resp = requests.get(map_url, map_params)
        if resp.status_code == 200:
            with open(map_filename, 'wb') as w:
                w.write(resp.content)
        print resp.status_code, map_url
        sleep(1)        
    with open(map_filename) as r:
        return r.read()

def get_route_map(route):
    map_filename = os.path.join(os.path.dirname(__file__), 'map_cache/route_'+route['route_id']+'.png')
    if not os.path.exists(map_filename):
        route_points = [leg['start'] for leg in route['legs']] + [route['legs'][-1]['end']]
        map_url = 'https://maps.googleapis.com/maps/api/staticmap'
        map_params = {'size': '330x350',
                      'markers': [ 'color:0x00F900|label:T|'+coord_to_str(p) for p in route_points ] ,
                      'path': ['color:0x00F900|weight:10|'+coord_to_str(leg['start'])+'|'+coord_to_str(leg['end']) for leg in route['legs']],
                      'key': GOOGLE_API_KEY,
                      }
        resp = requests.get(map_url, map_params)
        if resp.status_code == 200:
            with open(map_filename, 'wb') as w:
                w.write(resp.content)
        print resp.status_code, map_url
        sleep(1)        
    with open(map_filename) as r:
        return r.read()


    
ROUTES_DB = jload(os.path.join(os.path.dirname(__file__), 'routes.json'))
for route in ROUTES_DB:
    get_route_map(route)
ROUTES_DB = dict([(str(t['route_id']), t) for t in ROUTES_DB])

RAW_TRIPS_DB = jload(os.path.join(os.path.dirname(__file__), 'trips_2015-08-31_23_BRT.json'))
#for trip in RAW_TRIPS_DB:
#    get_trip_map(trip)
RAW_TRIPS_DB = dict([(str(t['raw_trip_id']), t) for t in RAW_TRIPS_DB if t['route_id'] in ROUTES_DB])



@app.route("/api/users/<user_id>/feed", methods=['GET'])
def feed(user_id):
    feed_items = []

    trips = [trip for trip in MONGO_DB.trips.find({'user_id': user_id}) if trip['route_id'] in ROUTES_DB]
    if len(trips) == 0:
        for raw_trip in random.sample(RAW_TRIPS_DB.values(), 10):
            trip = deepcopy(raw_trip)
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


@app.route("/api/users/<user_id>/trips_for_route/<route_id>", methods=['GET'])
def trips_for_route(user_id, route_id):
    trips = [trip for trip in MONGO_DB.trips.find({'user_id': user_id, 'route_id': route_id})]
    for trip in trips:
        trip['trip_id'] = str(trip['_id'])
        del trip['_id']
    return Response(json.dumps(trips), mimetype='application/json')
    
    

    
@app.route("/api/trips/<trip_id>", methods=['GET'])
def trips(trip_id):
    trip = MONGO_DB.trips.find_one({'_id': ObjectId(trip_id)})
    trip['trip_id'] = str(trip['_id'])
    del trip['_id']
    return Response(json.dumps(trip), mimetype='application/json')



@app.route("/api/users/<user_id>/route_trip_counts", methods=['GET'])
def route_trip_counts(user_id):
    route_counts = MONGO_DB.trips.aggregate([
        {"$match" : { 'user_id' : user_id } },
        {"$group" : {'_id':"$route_id", 'count':{ '$sum':1}}}
        ])
    route_counts = dict([(x['_id'], x['count']) for x in route_counts])
    return Response(json.dumps(route_counts), mimetype='application/json')
 

@app.route("/api/trips/<trip_id>/map", methods=['GET'])
def trip_map(trip_id):
    trip = MONGO_DB.trips.find_one({'_id': ObjectId(trip_id)})
    return Response(get_trip_map(RAW_TRIPS_DB[trip['raw_trip_id']]), mimetype='image/png')


@app.route("/api/users/<user_id>/routes", methods=['GET'])
def user_routes(user_id):
    route_ids = Counter([trip['route_id'] for trip in MONGO_DB.trips.find({'user_id': user_id}) if trip['route_id'] in ROUTES_DB])
    routes = [deepcopy(ROUTES_DB[route_id]) for route_id in route_ids.keys()]
    routes.sort(key=lambda route: route_ids[route['route_id']])
    routes.reverse()
    routes = routes[:5]
    return Response(json.dumps(routes), mimetype='application/json')
    

@app.route("/api/routes/all/<route_id>", methods=['GET'])
def routes(route_id):
    return Response(json.dumps(ROUTES_DB[route_id]), mimetype='application/json')

@app.route("/api/routes/all/<route_id>/map", methods=['GET'])
def route_map(route_id):
    return Response(get_route_map(ROUTES_DB[route_id]), mimetype='image/png')

@app.route("/api/routes/popular", methods=['GET'])
def popular_routes():
    route_counts = list(MONGO_DB.trips.aggregate([ {"$group" : {'_id':"$route_id", 'count':{ '$sum':1}}} ]))
    route_counts.sort(key=lambda x: x['count'])
    route_counts.reverse()
    route_counts = route_counts[:5]
    routes = [ROUTES_DB[x['_id']] for x in route_counts]
    return Response(json.dumps(routes), mimetype='application/json')


@app.route("/api/users/<user_id>/pledges", methods=['GET', 'POST'])
def user_pledges(user_id):
    if request.method in ['POST']:
        req = json.loads(request.get_data())
        print req
    else:
        req = {}  
    route_ids = req.get('route_ids') or [p['route_id'] for p in MONGO_DB.pledges.find({'user_id': user_id})]
    
    pledge_map = {}
    for route_id in route_ids:
        pledge_map[route_id] = {'total_count': 0, 'total_amount': 0.0, 'pledges': [], 'mine': False, 'mine_amount': 0.0 }

    for pledge in MONGO_DB.pledges.find({'route_id': { '$in': route_ids }}):
        del pledge['_id']
        route_id = pledge['route_id']
        pledge_map[route_id]['total_count'] = pledge_map[route_id]['total_count'] + 1
        pledge_map[route_id]['total_amount'] = pledge_map[route_id]['total_amount'] + pledge['amount']
        pledge_map[route_id]['pledges'].append(pledge)
        if pledge['user_id'] == user_id:
            pledge_map[route_id]['mine'] = True
            pledge_map[route_id]['mine_amount'] = pledge['amount']

    return Response(json.dumps(pledge_map), mimetype='application/json')
        
        
@app.route("/api/users/<user_id>/pledges/<route_id>", methods=['PUT', 'DELETE', 'GET'])
def route_pledges(user_id, route_id):
    if request.method in ['PUT']:
        req = json.loads(request.get_data())
        for k in ['_id', 'user_id', 'route_id']:
            if k in req:
                del req[k]
        MONGO_DB.pledges.update_one({'route_id': route_id, 'user_id': user_id}, {'$set': req}, upsert=True)
    elif request.method in ['DELETE']:
        MONGO_DB.pledges.delete_many({'route_id': route_id, 'user_id': user_id})
    
    current_pledge = MONGO_DB.pledges.find_one({'route_id': route_id, 'user_id': user_id}) or {'_id': -1, 'route_id': route_id, 'user_id': user_id, 'amount': 0}
    del current_pledge['_id']

    return Response(json.dumps(current_pledge), mimetype='application/json')
        
        
    
    

    
    

@app.route("/api/reset", methods=['GET'])
def reset():
    MONGO_DB.trips.drop()
    MONGO_DB.pledges.drop()
    return Response(json.dumps({'status': 'reset_complete'}), mimetype='application/json')
    
    




    
if __name__ == "__main__":
    app.run('0.0.0.0', 3000, debug=True)
