import threading
import logging
import os
import base64
from mqtt_service.pub_client import MQTTStreamPubBase


class MQTTStreamPub(MQTTStreamPubBase):
    def __init__(self):
        MQTTStreamPubBase.__init__(self, "vspc")

    def vspc_out_pub(self, key, data):
        topic = "VSPC_STREAM/{0}/OUT".format(key)
        payload = base64.b64encode(data)
        return self.publish(topic=topic, payload=payload, qos=1)

    def vspc_in_pub(self, key, data):
        topic = "VSPC_STREAM/{0}/IN".format(key)
        payload = base64.b64encode(data)
        return self.publish(topic=topic, payload=payload, qos=1)

    def socket_out_pub(self, key, data):
        topic = "SOCKET_STREAM/{0}/OUT".format(key)
        payload = base64.b64encode(data)
        return self.publish(topic=topic, payload=payload, qos=1)

    def socket_in_pub(self, key, data):
        topic = "SOCKET_STREAM/{0}/IN".format(key)
        payload = base64.b64encode(data)
        return self.publish(topic=topic, payload=payload, qos=1)

    def vspc_status(self, key, info):
        topic = "VSPC_STATUS/{0}".format(key)
        return self.publish(topic=topic, payload=info, qos=1)
