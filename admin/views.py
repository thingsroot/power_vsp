import logging
import uuid
from admin import app
from flask import json, jsonify, request, make_response
from helper import _dict

@app.route("/")
def index():
    # resp = make_response(render_template(...))
    # resp.set_cookie('username', 'the username')
    # return resp
    return "Power Virtual Serial Port!!"


@app.route("/v1/vspc/api/<method>", methods=['POST', 'GET'])
def vspc_api(method):
    service = app.vspc_service
    api_method = "{0}_{1}".format('api', method)
    payload = _dict(request.args)
    response = {}
    if request.method == 'POST':
        payload = _dict(json.loads(request.data))
    id = payload.get("id") or uuid.uuid1()
    try:
        service.is_whitelisted(api_method)
        response = getattr(service, api_method)(id, payload)
    except Exception as ex:
        logging.exception(ex)
        response = service.failure("api", id, repr(ex))

    return jsonify(response)

