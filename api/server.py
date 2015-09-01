import os
import sys
sys.path.append(os.path.dirname(__file__))

import json
import dateutil.parser
import re
import random

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

TRIPS_DB = jload(os.path.join(os.path.dirname(__file__), 'routes_2015-08-31_23_BRT.json'))
for i, t in enumerate(TRIPS_DB):
    t['trip_id'] = str(i)
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


    
if __name__ == "__main__":
    app.run('0.0.0.0', 3000, debug=True)
