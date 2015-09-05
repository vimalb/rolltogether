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
from datetime import datetime, timedelta
import pytz
import urllib

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

TRIP_ICON_URLS = {
    'trip-start-home': 'http://goo.gl/sWSDFa',
    'trip-start-work': 'http://goo.gl/RG2kNl',
    'trip-start-errand': 'http://goo.gl/PS4Dor',
    'trip-start-friend': 'http://goo.gl/8uGb5R',
    'trip-end-home': 'http://goo.gl/Rt3GUW',
    'trip-end-work': 'http://goo.gl/Nid5Bb',
    'trip-end-errand': 'http://goo.gl/9L3o9I',
    'trip-end-friend': 'http://goo.gl/1IsuaC',
    }

def get_trip_map(trip):
    map_filename = os.path.join(os.path.dirname(__file__), 'map_cache/trip_'+trip['raw_trip_id']+'.png')
    if not os.path.exists(map_filename):
        start_pos = trip['legs'][0]['start']
        finish_pos = trip['legs'][-1]['end']
        start_icon_url = TRIP_ICON_URLS['trip-start-'+trip['start_point_info']['type']]
        end_icon_url = TRIP_ICON_URLS['trip-end-'+trip['end_point_info']['type']]
        path = []
        for leg in trip['legs']:
            leg_color = '0x6060FBFF'

            if (leg['warning_level'] == 'Clear') and (leg['nominal_kmph'] > 75.0):
              leg_color = '0x10FF00FF'
            elif (leg['warning_level'] == 'Clear') and (leg['nominal_kmph'] <= 75.0) and (leg['nominal_kmph'] > 65.0):
              leg_color = '0x40FF00FF'
            elif (leg['warning_level'] == 'Clear') and (leg['nominal_kmph'] <= 65.0) and (leg['nominal_kmph'] > 55.0):
              leg_color = '0x80FF00FF'
            elif (leg['warning_level'] == 'Clear') and (leg['nominal_kmph'] <= 55.0) and (leg['nominal_kmph'] > 45.0):
              leg_color = '0xC0FF00FF'
            elif (leg['warning_level'] == 'Clear') and (leg['nominal_kmph'] <= 45.0) and (leg['nominal_kmph'] > 35.0):
              leg_color = '0xFFFF00FF'
            elif (leg['warning_level'] == 'Clear') and (leg['nominal_kmph'] <= 35.0) and (leg['nominal_kmph'] > 25.0):
              leg_color = '0xFFC000FF'
            elif (leg['warning_level'] == 'Clear') and (leg['nominal_kmph'] <= 25.0):
              leg_color = '0xFF8000FF'
            elif (leg['warning_level'] == 'Low Impact'):
              leg_color = '0xFFFF00FF'
            elif (leg['warning_level'] == 'Minor'):
              leg_color = '0xFFFF00FF'
            elif (leg['warning_level'] == 'Moderate'):
              leg_color = '0x10FF00FF'
            elif (leg['warning_level'] == 'Serious'):
              leg_color = '0x10FF00FF'
            
            path.append('weight:8|color:'+leg_color+'|'+coord_to_str(leg['start'])+'|'+coord_to_str(leg['end']))
            
        map_url = 'https://maps.googleapis.com/maps/api/staticmap'
        map_params = {'size': '330x350',
                      'markers': [ 'icon:'+start_icon_url+'|'+coord_to_str(start_pos), 'icon:'+end_icon_url+'|'+coord_to_str(finish_pos)],
                      'path': path,
                      'key': GOOGLE_API_KEY,
                      }
        resp = requests.get(map_url, map_params)
        if resp.status_code == 200:
            with open(map_filename, 'wb') as w:
                w.write(resp.content)
        print resp.status_code, resp.url
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
for trip in RAW_TRIPS_DB:
    get_trip_map(trip)
RAW_TRIPS_DB = dict([(str(t['raw_trip_id']), t) for t in RAW_TRIPS_DB if t['route_id'] in ROUTES_DB])

def utcnow():
    return datetime.utcnow().replace(tzinfo=pytz.UTC)

def localnow():
    return datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Brazil/East'))

def between(x,a,b):
    return x >= a and x < b

def fuzzify(raw_trip_id, target_time):
    trip = deepcopy(RAW_TRIPS_DB[raw_trip_id])
    trip['local_timestamp'] = target_time.astimezone(pytz.timezone('Brazil/East')).isoformat()
    return trip

def reverse_trip_id(raw_trip_id):
    return random.choice(RAW_TRIPS_DB[raw_trip_id]['trips_return_to_start'])

def seed_trip_history(user_id):
    now = localnow()
    trip_seed = MONGO_DB.trip_seeds.find_one({'user_id': user_id})
    if not trip_seed:
        trip_seed = { 'user_id': user_id,
                      'commute_raw_trip_id': random.choice([t['raw_trip_id'] for t in RAW_TRIPS_DB.values() if t['start_point_info']['type'] == 'home' and t['end_point_info']['type'] == 'work']),
                    }
        MONGO_DB.trip_seeds.insert_one(trip_seed)
        print "Created seed for user_id", user_id
    print "Using seed", trip_seed

    MONGO_DB.trips.delete_many({'user_id': user_id})

    commute_trip = RAW_TRIPS_DB[trip_seed['commute_raw_trip_id']]
    add_trips = []

    # Today trips
    add_trips.append(fuzzify(random.choice(commute_trip['trips_same_start_fun']), now-timedelta(hours=2)))

    # Past month daily trips
    yesterday = (now-timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
    for i in range(30):
        ref_day = yesterday - timedelta(days=i)
        if ref_day.isoweekday() in [1, 2, 4, 5]:
            add_trips.append(fuzzify(commute_trip['raw_trip_id'], ref_day+timedelta(hours=7)))
            add_trips.append(fuzzify(reverse_trip_id(commute_trip['raw_trip_id']), ref_day+timedelta(hours=17)))
            if random.random() < 0.5:
                fun_trip_id = random.choice(commute_trip['trips_same_start_fun'])
                add_trips.append(fuzzify(fun_trip_id, ref_day+timedelta(hours=19)))
                #add_trips.append(fuzzify(reverse_trip_id(fun_trip_id), ref_day+timedelta(hours=20)))
                
    for trip in add_trips:
        trip['user_id'] = user_id
    MONGO_DB.trips.insert_many(add_trips)
    
    


@app.route("/api/users/<user_id>/feed", methods=['GET'])
def feed(user_id):
    trips = list(MONGO_DB.trips.find({'user_id': user_id}))
    now = localnow()
    today_start = now.replace(hour=0,minute=0,second=0,microsecond=0)
    
    today_trips = [t for t in trips if dateutil.parser.parse(t['local_timestamp']) >= today_start]
    if len(today_trips) == 0:
        seed_trip_history(user_id)
        trips = list(MONGO_DB.trips.find({'user_id': user_id}))

    feed_items = []
    for trip in trips:
        trip['trip_id'] = str(trip['_id'])
        del trip['_id']
        feed_items.append({'item_type': 'my_trip',
                           'item_id': trip['trip_id'],
                           'item_details': trip,
                           'item_local_timestamp': trip['local_timestamp'],
                           })

    feed_items.sort(key=lambda f: dateutil.parser.parse(f['item_local_timestamp']))
    feed_items.reverse()

    today_items = [f for f in feed_items if dateutil.parser.parse(f['item_local_timestamp']) >= today_start]
    this_week_items = [f for f in feed_items if between(dateutil.parser.parse(f['item_local_timestamp']), today_start-timedelta(days=7), today_start)]
    
    feed_items = []
    feed_items.append({'item_type': 'feed_divider', 'item_details': {'name': 'Today', 'item_count': len(today_items)}})
    feed_items = feed_items + today_items
    feed_items.append({'item_type': 'feed_divider', 'item_details': {'name': 'Past Week', 'item_count': len(this_week_items)}})
    feed_items = feed_items + this_week_items
        
    return Response(json.dumps(feed_items), mimetype='application/json')


@app.route("/api/users/<user_id>/trips_for_route/<route_id>", methods=['GET'])
def trips_for_route(user_id, route_id):
    trips = [trip for trip in MONGO_DB.trips.find({'user_id': user_id, 'route_id': route_id})]
    for trip in trips:
        trip['trip_id'] = str(trip['_id'])
        del trip['_id']
    return Response(json.dumps(trips), mimetype='application/json')
    
    

    
@app.route("/api/trips/<trip_id>", methods=['GET'])
def rips(trip_id):
    trip = MONGO_DB.trips.find_one({'_id': ObjectId(trip_id)})
    trip['trip_id'] = str(trip['_id'])
    del trip['_id']
    return Response(json.dumps(trip), mimetype='application/json')



@app.route("/api/users/<user_id>/route_trip_counts", methods=['GET', 'POST'])
def route_trip_counts(user_id):
    if request.method in ['POST']:
        req = json.loads(request.get_data())
    else:
        req = {}  
    query = []
    route_ids = req.get('route_ids') or []
    if route_ids:
        query.append({"$match" : {'route_id': { '$in': route_ids }} })
    query.append({"$group" : {'_id':"$route_id", 'count':{ '$sum':1}}})
    
    self_route_counts = MONGO_DB.trips.aggregate([
        {"$match" : { 'user_id' : user_id } },
        ] + query)
    all_route_counts = MONGO_DB.trips.aggregate(query)
    
    route_counts = {}
    for route_id in route_ids:
        route_counts[route_id] = {'mine': 0, 'total': 0}
    for result in self_route_counts:
        route_id = result['_id']
        if route_id not in route_counts:
            route_counts[route_id] = {'mine': 0, 'total': 0}
        route_counts[route_id]['mine'] = result['count']
    for result in all_route_counts:
        route_id = result['_id']
        if route_id not in route_counts:
            route_counts[route_id] = {'mine': 0, 'total': 0}
        route_counts[route_id]['total'] = result['count']

    return Response(json.dumps(route_counts), mimetype='application/json')
 

@app.route("/api/trips/<trip_id>/map", methods=['GET'])
def trip_map(trip_id):
    trip = MONGO_DB.trips.find_one({'_id': ObjectId(trip_id)})
    return Response(get_trip_map(RAW_TRIPS_DB[trip['raw_trip_id']]), mimetype='image/png')


@app.route("/api/users/<user_id>/routes", methods=['GET'])
def user_routes(user_id):
    route_ids = Counter([trip['route_id'] for trip in MONGO_DB.trips.find({'user_id': user_id}) if trip['route_id'] in ROUTES_DB])
    routes = [deepcopy(ROUTES_DB[route_id]) for route_id in route_ids.keys() if route_ids[route_id] > 1]
    routes.sort(key=lambda route: route_ids[route['route_id']])
    routes.reverse()
    routes = routes[:3]
    return Response(json.dumps(routes), mimetype='application/json')
    

@app.route("/api/routes/all/<route_id>", methods=['GET'])
def routes(route_id):
    return Response(json.dumps(ROUTES_DB[route_id]), mimetype='application/json')

@app.route("/api/routes/all/<route_id>/map", methods=['GET'])
def route_map(route_id):
    return Response(get_route_map(ROUTES_DB[route_id]), mimetype='image/png')

@app.route("/api/routes/popular", methods=['GET'])
def popular_routes():
    route_counts = [c for c in MONGO_DB.trips.aggregate([ {"$group" : {'_id':"$route_id", 'count':{ '$sum':1}}} ]) if c['count'] > 1]
    route_counts.sort(key=lambda x: x['count'])
    route_counts.reverse()
    route_counts = route_counts[:3]
    routes = [ROUTES_DB[x['_id']] for x in route_counts]
    return Response(json.dumps(routes), mimetype='application/json')


@app.route("/api/users/<user_id>/pledges", methods=['GET', 'POST'])
def user_pledges(user_id):
    if request.method in ['POST']:
        req = json.loads(request.get_data())
    else:
        req = {}  
    route_ids = req.get('route_ids') or [p['route_id'] for p in MONGO_DB.pledges.find({'user_id': user_id})]
    
    pledge_map = {}
    for route_id in route_ids:
        pledge_map[route_id] = {'total_count': 0, 'total_amount': 0.0, 'pledges': [], 'mine': False, 'mine_amount': 0.0 }

    for pledge in MONGO_DB.pledges.find({'route_id': { '$in': route_ids }}):
        del pledge['_id']
        route_id = pledge['route_id']
        pledge_map[route_id]['route_id'] = route_id
        pledge_map[route_id]['user_id'] = user_id
        pledge_map[route_id]['name'] = ROUTES_DB[route_id]['name']
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
        req['local_timestamp'] = localnow().isoformat()
        MONGO_DB.pledges.update_one({'route_id': route_id, 'user_id': user_id}, {'$set': req}, upsert=True)
    elif request.method in ['DELETE']:
        MONGO_DB.pledges.delete_many({'route_id': route_id, 'user_id': user_id})
    
    current_pledge = MONGO_DB.pledges.find_one({'route_id': route_id, 'user_id': user_id}) or {'_id': -1, 'route_id': route_id, 'user_id': user_id, 'amount': 0}
    del current_pledge['_id']

    return Response(json.dumps(current_pledge), mimetype='application/json')
        


@app.route("/api/reset", methods=['GET'])
def reset():
    if request.args.get('key') != 'kwyjibo':
        return Response(json.dumps({'status': 'reset ignored'}), mimetype='application/json')
    
    MONGO_DB.trip_seeds.drop()
    MONGO_DB.trip_seeds.create_index('user_id')

    MONGO_DB.trips.drop()
    MONGO_DB.trips.create_index('user_id')
    MONGO_DB.trips.create_index('route_id')

    MONGO_DB.pledges.drop()
    MONGO_DB.pledges.create_index('user_id')
    MONGO_DB.pledges.create_index('route_id')

    now = localnow()
    user_ids = ['demo'+str(i) for i in range(100)]
    pledges = []
    for user_id in user_ids:
        seed_trip_history(user_id)
        my_routes = json.loads(user_routes(user_id).data)
        for route in my_routes:
            route_id = route['route_id']
            if random.random() < 0.9:
                pledges.append({'user_id': user_id,
                          'route_id': route_id,
                          'amount': random.choice([5.0, 20.0, 100.0]),
                          'local_timestamp': (now - timedelta(seconds=random.randint(3600*24*2, 3600*24*27))).isoformat(),
                          })
    for route in json.loads(popular_routes().data):
        route_id = route['route_id']
        for user_id in user_ids:
            if random.random() < 0.9:
                pledges.append({'user_id': user_id,
                          'route_id': route_id,
                          'amount': random.choice([5.0, 20.0, 100.0]),
                          'local_timestamp': (now - timedelta(seconds=random.randint(3600*24*2, 3600*24*27))).isoformat(),
                          })
    MONGO_DB.pledges.insert_many(pledges)
            
        
        

    return Response(json.dumps({'status': 'reset_complete',
                                'timestamp': utcnow().isoformat(),
                                'user_count': len(user_ids),
                                'pledge_count': len(pledges)
                                }), mimetype='application/json')
    
    




    
if __name__ == "__main__":
    app.run('0.0.0.0', 3000, debug=True)
