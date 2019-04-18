import threading
import logging
import os
import base64
import paho.mqtt.client as mqtt
from vspc_conf import MQTT_PROT


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    userdata.on_connect(client, flags, rc)


def on_disconnect(client, userdata, rc):
    userdata.on_disconnect(client, rc)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        userdata.on_message(client, msg)
    except Exception as ex:
        logging.exception(ex)


class MQTTStreamPub(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.host = "localhost"
        self.port = MQTT_PROT
        self.clientid = "STREAM_PUB"
        self.keepalive = 60
        self.sub_devs = set()

    def stop(self):
        self.mqttc.disconnect()

    def run(self):
        try:
            mqttc = mqtt.Client(userdata=self, client_id=self.clientid)
            self.mqttc = mqttc

            mqttc.on_connect = on_connect
            mqttc.on_disconnect = on_disconnect
            mqttc.on_message = on_message

            logging.debug('MQTT Connect to %s:%d cid: %s', self.host, self.port, self.clientid)
            mqttc.connect_async(self.host, self.port, self.keepalive)

            mqttc.loop_forever(retry_first_connection=True)
        except Exception as ex:
            logging.exception(ex)
            os._exit(1)

    def on_connect(self, client, flags, rc):
        logging.info("MQTT %s connected return %d", self.host, rc)

    def on_disconnect(self, client, rc):
        logging.info("MQTT %s disconnect return %d", self.host, rc)

    def on_message(self, client, msg):
        logging.info("MQTT %s message recevied topic %s", self.host, msg.topic)

    def vspc_out_pub(self, key, data):
        topic = "VSPC_STREAM/{0}/OUT".format(key)
        payload = base64.b64encode(data)
        return self.mqttc.publish(topic=topic, payload=payload, qos=1)

    def vspc_in_pub(self, key, data):
        topic = "VSPC_STREAM/{0}/IN".format(key)
        payload = base64.b64encode(data)
        return self.mqttc.publish(topic=topic, payload=payload, qos=1)

    def socket_out_pub(self, key, data):
        topic = "SOCKET_STREAM/{0}/OUT".format(key)
        payload = base64.b64encode(data)
        return self.mqttc.publish(topic=topic, payload=payload, qos=1)

    def socket_in_pub(self, key, data):
        topic = "SOCKET_STREAM/{0}/IN".format(key)
        payload = base64.b64encode(data)
        return self.mqttc.publish(topic=topic, payload=payload, qos=1)

    def vspc_status(self, key, info):
        topic = "VSPC_STATUS/{0}".format(key)
        return self.mqttc.publish(topic=topic, payload=info, qos=1)


