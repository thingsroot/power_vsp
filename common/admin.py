import logging
import uuid
from flask import Blueprint, current_app
from flask import json, jsonify, request, make_response
from helper import _dict

update_admin = Blueprint("update", __name__)


@update_admin.route("/v1/update/api/<method>", methods=['POST', 'GET'])
def update_api(method):
    service = current_app.services.get('update_service')
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
