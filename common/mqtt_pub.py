import threading
import logging
import os
import base64
from mqtt_service.pub_client import MQTTStreamPubBase


class MQTTStreamPub(MQTTStreamPubBase):
    def __init__(self):
        MQTTStreamPubBase.__init__(self, "update")

    def proxy_status(self, key, info):
        topic = "PROXY_STATUS/{0}".format(key)
        return self.publish(topic=topic, payload=info, qos=1)

    def dest_status(self, key, info):
        topic = "DEST_STATUS/{0}".format(key)
        return self.publish(topic=topic, payload=info, qos=1)
