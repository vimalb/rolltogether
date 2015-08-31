import requests
import os
from copy import deepcopy
import json
from math import sqrt
from datetime import datetime
import pytz

URL_PARAMS = {'key': os.environ['BING_MAPS_KEY']}

ROUTES_URL = 'http://dev.virtualearth.net/REST/v1/Routes'

SEVERITIES = ['Clear','Low Impact', 'Minor', 'Moderate','Serious']

ROUTE_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'raw_route_cache.json')

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
    return sqrt(pow(a[0]-b[0],2)+pow(a[1]-b[1],2))

def closest(target, points):
    candidates = [(p, dist(p,target)) for p in points]
    candidates.sort(key=lambda x: x[1])
    point = candidates[0][0]
    distance = candidates[0][1]
    return point, distance



def get_route(start_lat_lon, end_lat_lon):
    url_params = deepcopy(URL_PARAMS)
    url_params['wp.0'] = ",".join([str(x) for x in start_lat_lon])
    url_params['wp.1'] = ",".join([str(x) for x in end_lat_lon])
    url_params['optmz'] = 'timeWithTraffic'
    url_params['ra'] = 'routePath'
    url_params['du'] = 'km'
    resp = requests.get(ROUTES_URL, params=url_params)
    resp_json = json.loads(resp.content)
    route_cache = jload(ROUTE_CACHE_FILE) if os.path.exists(ROUTE_CACHE_FILE) else []
    route_cache.append({'start_lat_lon': start_lat_lon,
                        'end_lat_lon': end_lat_lon,
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_url': ROUTES_URL,
                        'request_params': url_params,
                        'response_json': resp_json,
                        })
    jdump(route_cache, ROUTE_CACHE_FILE)
    info = resp_json['resourceSets'][0]['resources'][0]
    path = [tuple(coord) for coord in info['routePath']['line']['coordinates']]
    itinerary = info['routeLegs'][0]['itineraryItems']
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
                     'warning_level': warning_level,
                     'nominal_kmph': nominal_kmph,
                     })
        active_warning = None if [w for w in warnings if w['path_end'] == leg_start] else active_warning
    total_distance_km = info['travelDistance']
    total_nominal_duration_min = info['travelDuration'] / 60.0
    total_actual_duration_min = info['travelDurationTraffic'] / 60.0
    route = {'timestamp': datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat(),
             'legs': legs,
             'total_distance_km': total_distance_km,
             'total_nominal_duration_min': total_nominal_duration_min,
             'total_actual_duration_min': total_actual_duration_min,
             }
    return route


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


route_timestamp = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Brazil/East'))
route_filename = os.path.join(os.path.dirname(__file__), 'routes_'+route_timestamp.strftime("%Y-%m-%d_%H-%M-%S_%Z")+'.json')

routes = []
for start, end in paths:
    print "Routing from", start, "to", end
    route = get_route(start, end)
    route['local_timestamp'] = route_timestamp.isoformat()
    routes.append(route)
    jdump(routes, route_filename)

