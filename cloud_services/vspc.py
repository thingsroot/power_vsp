import threading
import logging
from llama import mqtt

API_RESULT = "@api/RESULT"
API_LIST = "@api/list"


class VSPC_Service(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def start(self):
        # Connect to MQTT broker and start dispatch loop
        dispatch, receive = mqtt.connect("localhost:1883", {
            "api": "v1/vspc/api",
        })

        for action in receive():
            if action["type"] == API_LIST:
                dispatch(self._handle_list(action["payload"]))

        threading.Thread.start(self)

    def api_failure(self, error_msg):
        return {
            "type": API_RESULT,
            "payload": {
                "result": False,
                "error": error_msg
            },
        }

    def api_success(self, result, data):
        return {
            "type": API_RESULT,
            "payload": {
                "result": result,
                "data": data
            },
        }

    def _handle_list(self, params):
        try:
            logging.info("Reversing string: {}".format(params))
            return self.api_success(True, params)
        except Exception as ex:
            return self.api_failure(repr(ex))
