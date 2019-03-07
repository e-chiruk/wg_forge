#!flask/bin/python

from flask import Flask, g, jsonify, request, abort, Response
from db_helper import Cats, CatColorsInfo, CatsStat
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import default_exceptions
import json
import psycopg2
import config

def make_app(import_name, **kwargs):
    def error_handler(ex):
        response = jsonify(message=str(ex))
        response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)
        return response

    application = Flask(import_name, **kwargs)

    for code in default_exceptions.items():
        application.error_handler_spec[code] = error_handler

    return application

app = make_app(__name__)

def json_dumps_default(obj):
    return str(obj)

def validate_cat():
    if not request.json:
        abort(400, 'Invalid JSON')
    keys = sorted(('name', 'color', 'tail_length', 'whiskers_length'))
    if sorted(request.json.keys()) != keys:
        abort(400, 'Invalid JSON')
    for key in keys:
        if not request.json[key]:
            abort(400, 'Invalid data in JSON')
    if request.json['color'] not in g.cats.get_colors():
        abort(400, 'Invalid color')
    if isinstance(request.json['tail_length'], int) and isinstance(request.json['whiskers_length'], int):
        if int(request.json['tail_length']) < 0 or int(request.json['whiskers_length']) < 0:
            abort(400, 'Invalid cat data')
    else:
        abort(400, 'Invalid cat data')
    if g.cats.find(request.json['name']):
        abort(400, 'Сat with {} name exists'.format(request.json['name']))

@app.before_request
def setup_request():
    g.db = psycopg2.connect("dbname='{0}' user='{1}' password='{2}' host='{3}' port='{4}'".format(config.dbname, config.user, config.password, config.host, config.port))
    g.cats = Cats(g.db)
    g.colors_info = CatColorsInfo(g.db)
    g.cats_stat = CatsStat(g.db)

@app.teardown_request
def teardown_request(exeption):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/ping', methods=['GET'])
def ping():
    return "Cats Service. Version 0.1"

@app.route('/get_cat_colors_info', methods=['GET'])
def get_color_info():
    return jsonify(items=g.colors_info.get_color_info())

@app.route('/get_cats_stat', methods=['GET'])
def get_cats_stat():
    return json.dumps(g.cats_stat.get_cats_stat(), default=json_dumps_default)

@app.route('/cats', methods=['GET'])
def get_cats():
    attribute = None
    order = None
    limit = None
    offset =None
    if len(request.args) > 0:
        params = ['attribute', 'order', 'limit', 'offset']
        for param in request.args.keys():
            if param not in params:
                abort(400, 'Non-existent parameter: {}'.format(param))
        if request.args.get('attribute') is not None:
            if request.args.get('order') is None:
                abort(400, 'Order is required')
            if request.args.get('attribute') not in g.cats.get_attributes():
                abort(400, 'Non-existent attribute: {}'.format(request.args.get('attribute')))
            order = str(request.args.get('order')).upper()
            attribute = str(request.args.get('attribute'))
            if order != 'ASC':
                if order != 'DESC':
                    abort(400, 'Invalid order')
        if request.args.get('limit') is not None:
            if request.args.get('offset') is None:
                abort(400, 'Offset is required')
            try:
                limit = int(request.args.get('limit'))
                offset = int(request.args.get('offset'))
            except ValueError:
                abort(400, 'Invalid parameter')
            if offset >= g.cats.count():
                abort(400, 'Invalid offset')
    return jsonify(items=g.cats.all(attribute, order, limit, offset))

@app.route('/cat', methods=['POST'])
def post_cat():
    validate_cat()
    g.cats.add(**request.json)
    return Response(status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5090, debug=True)