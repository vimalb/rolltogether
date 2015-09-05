import requests
import os
from copy import deepcopy
import json
from math import sqrt
from datetime import datetime
import pytz
import dateutil.parser
import random
from geopy.distance import great_circle

URL_PARAMS = {'key': os.environ['BING_MAPS_KEY']}

ROUTES_URL = 'http://dev.virtualearth.net/REST/v1/Routes'

SEVERITIES = ['Clear','Low Impact', 'Minor', 'Moderate','Serious']

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

TRIP_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'raw_trip_cache.json')

def jdump(jval, filename):
    jdir = os.path.dirname(filename)
    if jdir and not os.path.exists(jdir):
        os.makedirs(jdir)
    with open(filename, 'w') as w:
        json.dump(jval, w, indent=2)

def jload(filename):
    with open(filename, 'r') as r:
        return json.load(r)    


def dist(a,b):
    return great_circle(a,b).meters

def closest(target, points):
    candidates = [(p, dist(p,target)) for p in points]
    candidates.sort(key=lambda x: x[1])
    point = candidates[0][0]
    distance = candidates[0][1]
    return point, distance


def convert_response_to_trip(resp_json):
    info = resp_json['resourceSets'][0]['resources'][0]
    itinerary = info['routeLegs'][0]['itineraryItems']
    
    raw_path = [tuple(coord) for coord in info['routePath']['line']['coordinates']]
    path = raw_path
    path_cutoff = max(20, len(itinerary))
    for generalization in info['routePath']['generalizations']:
        proposed_path = [raw_path[i] for i in generalization['pathIndices']]
        if (len(proposed_path) < len(path)) and (len(path) > path_cutoff):
            path = proposed_path
        elif (len(proposed_path) > len(path)) and (len(proposed_path) <= path_cutoff):
            path = proposed_path
    for itin in itinerary:
        itin['path_start'] = closest(itin['maneuverPoint']['coordinates'], path)[0]
    warnings = [w for itin in itinerary for w in itin.get('warnings',[]) if w.get('origin') and w.get('to') and w.get('severity') in SEVERITIES]
    for w in warnings:
        endpoints = [closest(tuple([float(f) for f in w['origin'].split(',')]), path)[0], closest(tuple([float(f) for f in w['to'].split(',')]), path)[0]]
        endpoints.sort(key=lambda x: path.index(x))
        w['path_start'] = endpoints[0]
        w['path_end'] = endpoints[1]
    legs = []
    active_itin = None
    active_warning = None
    for i in range(len(path)-1):
        leg_start = path[i]
        leg_end = path[i+1]
        active_itin = ([i for i in itinerary if i['path_start'] == leg_start] + [active_itin])[0]
        active_warning = ([w for w in warnings if w['path_start'] == leg_start] + [active_warning])[0]
        warning_level = active_warning['severity'] if active_warning else SEVERITIES[0]
        nominal_kmph = active_itin['travelDistance'] * 3600.0 / active_itin['travelDuration']
        legs.append({'start': leg_start,
                     'end': leg_end,
                     'distance_km': dist(leg_start, leg_end) / 1000,
                     'warning_level': warning_level,
                     'nominal_kmph': nominal_kmph,
                     })
        active_warning = None if [w for w in warnings if w['path_end'] == leg_start] else active_warning
    total_distance_km = info['travelDistance']
    total_nominal_duration_min = info['travelDuration'] / 60.0
    total_actual_duration_min = info['travelDurationTraffic'] / 60.0
    trip = {'timestamp': datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat(),
             'legs': legs,
             'total_distance_km': total_distance_km,
             'total_nominal_duration_min': total_nominal_duration_min,
             'total_actual_duration_min': total_actual_duration_min,
             }
    return trip
    


def get_trip(start_lat_lon, end_lat_lon):
    url_params = deepcopy(URL_PARAMS)
    url_params['wp.0'] = ",".join([str(x) for x in start_lat_lon])
    url_params['wp.1'] = ",".join([str(x) for x in end_lat_lon])
    url_params['optmz'] = 'timeWithTraffic'
    url_params['ra'] = 'routePath'
    url_params['du'] = 'km'
    url_params['tl'] = '0.0001,0.001,0.01'
    resp = requests.get(ROUTES_URL, params=url_params)
    if resp.status_code != 200:
        return None
    resp_json = json.loads(resp.content)
    trip_cache = jload(TRIP_CACHE_FILE) if os.path.exists(TRIP_CACHE_FILE) else []
    trip_cache.append({'start_lat_lon': start_lat_lon,
                        'end_lat_lon': end_lat_lon,
                        'timestamp': datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat(),
                        'request_url': ROUTES_URL,
                        'request_params': url_params,
                        'response_json': resp_json,
                        })
    jdump(trip_cache, TRIP_CACHE_FILE)
    return convert_response_to_trip(resp_json)


destinations = [(-23.51557, -46.73141),
(-23.61608, -46.73915),
(-23.52287, -46.68808),
(-23.55568, -46.69164),
(-23.55623, -46.68039),
(-23.59117, -46.68209),
(-23.58168, -46.66702),
(-23.62294, -46.67053),
(-23.58741, -46.65763),
(-23.56164, -46.64291),
(-23.60945, -46.61405),
(-23.5586, -46.60948),
(-23.54424, -46.62773),
(-23.53426, -46.63392),
(-23.53415, -46.64002)]

paths = []
for start in destinations:
    for end in destinations:
        if(dist(start, end) > 0.06):
            paths.append([start, end])


"""
for start, end in paths:
    print "Routing from", start, "to", end
    get_trip(start, end)
"""

trip_cache = jload(TRIP_CACHE_FILE)
trip_cache = [r for r in trip_cache if r['response_json'].get('statusCode') == 200]
trip_files = {}
for raw_trip in trip_cache:
    trip_timestamp = dateutil.parser.parse(raw_trip['timestamp']).astimezone(pytz.timezone('Brazil/East'))
    trip_filename = os.path.join(os.path.dirname(__file__), 'trips_'+trip_timestamp.strftime("%Y-%m-%d_%H_%Z")+'.json')
    if trip_filename not in trip_files:
        trip_files[trip_filename] = []
    resp_json = raw_trip['response_json']
    trip = convert_response_to_trip(resp_json)
    trip_files[trip_filename].append(trip)

for trip_filename, trips in trip_files.iteritems():
    jdump(trips, trip_filename)

route_points = []
for trips in trip_files.values():
    for trip in trips:
        for leg in trip['legs']:
            start = tuple(leg['start'])
            end = tuple(leg['end'])
            if start not in route_points:
                route_points.append(start)
            if end not in route_points:
                route_points.append(end)

random.shuffle(route_points)

def calc_transit_points(route_points, threshold_meters):
    transit_points = {route_points[0]: []}
    for route_point in route_points:
        closest_point, distance = closest(route_point, transit_points.keys())
        if distance < threshold_meters:
            transit_points[closest_point].append(route_point)
        else:
            transit_points[route_point] = [route_point]
    return transit_points

TRANSIT_POINTS = calc_transit_points(route_points, 3000)

TRANSIT_POINT_INFO = [
    { 'point': (-23.5166, -46.726709),
      'name': 'Name 1',
      'area': 'Area 1'
        },
    { 'point': (-23.586487, -46.690038),
      'name': 'Name 2',
      'area': 'Area 2'
        },
    { 'point': (-23.630889, -46.644328),
      'name': 'Name 3',
      'area': 'Area 3'
        },
    { 'point': (-23.526561, -46.630182),
      'name': 'Name 4',
      'area': 'Area 4'
        },
    { 'point': (-23.607838, -46.614008),
      'name': 'Name 5',
      'area': 'Area 5'
        },
    { 'point': (-23.630277, -46.734868),
      'name': 'Name 6',
      'area': 'Area 6'
        },
    { 'point': (-23.559982, -46.712408),
      'name': 'Name 7',
      'area': 'Area 7'
        },
    { 'point': (-23.61435, -46.70089),
      'name': 'Name 8',
      'area': 'Area 8'
        },
    { 'point': (-23.619757, -46.671321),
      'name': 'Name 9',
      'area': 'Area 9'
        },
    { 'point': (-23.57953, -46.599857),
      'name': 'Name 10',
      'area': 'Area 10'
        },
    { 'point': (-23.604007, -46.74741),
      'name': 'Name 11',
      'area': 'Area 11'
        },
    { 'point': (-23.51433, -46.677979),
      'name': 'Name 12',
      'area': 'Area 12'
        },
    { 'point': (-23.552289, -46.658608),
      'name': 'Name 13',
      'area': 'Area 13'
        },
    { 'point': (-23.556001, -46.623031),
      'name': 'Name 14',
      'area': 'Area 14'
        },
    { 'point': (-23.585318, -46.654971),
      'name': 'Name 15',
      'area': 'Area 15'
        },
    ]
TRANSIT_POINT_INFO = dict([ (p['point'],p) for p in TRANSIT_POINT_INFO ])

TRANSIT_POINTS = list(TRANSIT_POINT_INFO.keys())

raw_trip_id = 0

all_trips = []
routes = []

TRANSIT_KMPH = 50.0
for trip_filename in trip_files.keys():
    trips = jload(trip_filename)
    for trip in trips:
        leg_points = [l['start'] for l in trip['legs']] + [trip['legs'][-1]['end']]
        leg_transit_points = []
        for leg_point in leg_points:
            leg_transit_point, distance = closest(leg_point, TRANSIT_POINTS)
            if leg_transit_point not in leg_transit_points:
                leg_transit_points.append(tuple(leg_transit_point))
        if len(leg_transit_points) > 1:
            transit_legs = [{'start': leg_transit_points[i],
                            'end': leg_transit_points[i+1],
                            'distance_km': dist(leg_transit_points[i], leg_transit_points[i+1]) / 1000,
                            'nominal_kmph': TRANSIT_KMPH,
                         } for i in range(len(leg_transit_points) - 1)]
            trip['transit_legs'] = transit_legs
            transit_km = sum([l['distance_km'] for l in transit_legs])
            trip['transit_distance_km'] = transit_km
            avg_kmph = trip['total_distance_km'] * 60.0 / trip['total_nominal_duration_min']
            remaining_km = trip['total_distance_km'] - transit_km
            trip['total_transit_duration_min'] = (transit_km / TRANSIT_KMPH)*60.0 + (remaining_km / avg_kmph)*60.0
            trip['total_trip_cost_real'] = trip['total_distance_km'] * 0.62 / 30.0 * 4 * 3.11
            trip['transit_trip_cost_real'] = remaining_km * 0.62 / 30.0 * 4 * 3.11 + 1
            
            trip['raw_trip_id'] = str(raw_trip_id)
            raw_trip_id = raw_trip_id + 1
            print "saved", (trip['total_actual_duration_min'] - trip['total_transit_duration_min']) * 100.0 / trip['total_actual_duration_min'], "minutes"
            print "saved", (trip['total_trip_cost_real'] - trip['transit_trip_cost_real']), " R$"

            matching_route = None
            for route in routes:
                route_transit_points = set([tuple(l['start']) for l in route['legs']] + [tuple(route['legs'][-1]['end'])])
                overlap = set(leg_transit_points).intersection(route_transit_points)
                if len(overlap) == len(route_transit_points):
                    route['legs'] = trip['transit_legs']
                    matching_route = route
                elif len(overlap) == len(leg_transit_points):
                    matching_route = route
            if not matching_route:
                matching_route = {'route_id': str(len(routes)),
                                  'legs': trip['transit_legs'],
                                  }
                routes.append(matching_route)
            trip['route_id'] = matching_route['route_id']
            
    trips = [r for r in trips if r.get('transit_legs')]
    jdump(trips, trip_filename)
    all_trips = all_trips + trips

for route in routes:
    route['target_amount'] = 1000.0 * len(route['legs'])
    start_info = TRANSIT_POINT_INFO[route['legs'][0]['start']]
    end_info = TRANSIT_POINT_INFO[route['legs'][-1]['end']]
    route['driving_duration_min'] = 0
    route['transit_distance_km'] = 0
    route['transit_duration_min'] = 0
    route['transit_stop_count'] = len(route['legs'])
    
    for trip in all_trips:
        if trip['route_id'] != route['route_id']:
            continue
        route['driving_duration_min'] = max(route['driving_duration_min'], trip['total_actual_duration_min'])
        route['transit_distance_km'] = max(route['transit_distance_km'], trip['transit_distance_km'])
        route['transit_duration_min'] = max(route['transit_duration_min'], trip['total_transit_duration_min'])
    route['name'] = start_info['name'] + ' to ' + end_info['name']
    route['description'] = 'This route goes from '+start_info['area'] + ' to ' + end_info['area'] \
                           + ' and features '+str(len(route['legs']))+' stops.'
    
route_filename = os.path.join(os.path.dirname(__file__), 'routes.json')
jdump(routes, route_filename)





"""
def coord_to_str(coord):
    if type(coord) == list or type(coord) == tuple:
        return str(coord[0])+','+str(coord[1])
    else:
        return str(coord['latitude'])+','+str(coord['longitude'])

map_url = 'https://maps.googleapis.com/maps/api/staticmap'
map_params = {'size': '330x350',
              'markers': [ 'color:red|'+coord_to_str(tp) for tp in transit_points],
              'key': GOOGLE_API_KEY,
              }
with open('foo.png','wb') as w:
    resp = requests.get(map_url, map_params)
    w.write(resp.content)
"""
    

