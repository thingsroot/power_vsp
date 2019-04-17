import threading
import logging
import re
import uuid
from llama import mqtt

match_routes = re.compile(r'^@([^/]+)/(.+)$')

@staticmethod
def whitelist(f):
    f.whitelisted = True
    return f

class Forbidden(Exception):
    result = False
    error = "forbidden"
    description = (
        'You don\'t have the permission to access the requested resource. '
        'It is either read-protected or not readable by the server.'
    )


class NotFound(Exception):
    result = False
    error = "not_found"
    description = (
        'The requested URL was not found on the server.  '
        'If you entered the URL manually please check your spelling and '
        'try again.'
    )


class BaseService(threading.Thread):
    def __init__(self, mqtt_server, routes):
        self._mqtt_server = mqtt_server
        self._routes = routes
        threading.Thread.__init__(self)

    def start(self):
        # Connect to MQTT broker and start dispatch loop
        dispatch, receive = mqtt.connect(self._mqtt_server, self._routes)

        for action in receive():
            action_type = action["type"]
            payload = action.get("payload")
            ag = match_routes.match(action_type)
            if ag:
                ag = ag.groups()
                route_key = ag[0]
                api_method = ag[1]
                if api_method == 'RESULT':
                    # Skip Result topic
                    continue
                api_method = "{0}_{1}".format(route_key, ag[1])
                logging.debug("Action: {0}  Payload {1}".format(action, action.get("payload")))
                id = payload.get("id") or uuid.uuid1()
                try:
                    self.is_whitelisted(api_method)
                    if not payload:
                        logging.error("Json deocde failure!!")
                        dispatch(self.failure(route_key, "JSON Deoce Failure!"))
                    else:
                        dispatch(getattr(self, api_method)(id, payload))
                except Exception as ex:
                    logging.exception(ex)
                    dispatch(self.failure(route_key, id, repr(ex)))
            else:
                dispatch(self.failure(route_key, uuid.uuid1(), "Topic api missing"))

        threading.Thread.start(self)

    def is_whitelisted(self, method):
        fn = getattr(self, method, None)
        if not fn:
            raise NotFound("Method {0} not found".format(method))
        elif not getattr(fn, "whitelisted", False):
            raise Forbidden("Method {0} not whitelisted".format(method))
        return True

    def failure(self, route_key, id, error_msg):
        assert(route_key and self._routes[route_key])
        assert(id and error_msg)
        return {
            "type": "@{0}/RESULT".format(route_key),
            "payload": {
                "id": str(id),
                "result": False,
                "error": error_msg
            },
        }

    def success(self, route_key, id, data):
        assert(route_key and self._routes[route_key])
        assert(id and data)
        return {
            "type": "@{0}/RESULT".format(route_key),
            "payload": {
                "id": str(id),
                "result": True,
                "data": data
            },
        }
