import threading
import logging
import os
import base64
from mqtt_service.pub_client import MQTTStreamPubBase


class MQTTStreamPub(MQTTStreamPubBase):
    def __init__(self):
        MQTTStreamPubBase.__init__(self, "vnet")

    def vnet_out_pub(self, key, data):
        topic = "VNET_STREAM/{0}/OUT".format(key)
        payload = base64.b64encode(data)
        return self.publish(topic=topic, payload=payload, qos=1)

    def vnet_in_pub(self, key, data):
        topic = "VNET_STREAM/{0}/IN".format(key)
        payload = base64.b64encode(data)
        return self.publish(topic=topic, payload=payload, qos=1)

    def vnet_status(self, key, info):
        topic = "VNET_STATUS/{0}".format(key)
        return self.publish(topic=topic, payload=info, qos=1)

    def proxy_status(self, key, info):
        topic = "PROXY_STATUS/{0}".format(key)
        return self.publish(topic=topic, payload=info, qos=1)

    def dest_status(self, key, info):
        topic = "DEST_STATUS/{0}".format(key)
        return self.publish(topic=topic, payload=info, qos=1)
