import threading
import logging
import os
import base64
import time
import paho.mqtt.client as mqtt
from hbmqtt_broker.conf import MQTT_PROT


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


class MQTTStreamPubBase(threading.Thread):
    def __init__(self, service_name):
        threading.Thread.__init__(self)
        self.host = "localhost"
        self.port = MQTT_PROT
        self.clientid = "STREAM_PUB." + service_name
        self.keepalive = 60
        self.service_name = service_name
        self._close_connection = False

    def stop(self):
        self._close_connection = True
        self.mqttc.disconnect()

    def run(self):
        while not self._close_connection:
            try:
                mqttc = mqtt.Client(userdata=self, client_id=self.clientid)
                self.mqttc = mqttc

                mqttc.on_connect = on_connect
                mqttc.on_disconnect = on_disconnect
                mqttc.on_message = on_message

                logging.debug('MQTT (%s) Connect to %s:%d cid: %s', self.service_name, self.host, self.port, self.clientid)
                mqttc.connect_async(self.host, self.port, self.keepalive)

                mqttc.loop_forever(retry_first_connection=True)
            except Exception as ex:
                logging.exception(ex)
                mqttc.disconnect()

    def on_connect(self, client, flags, rc):
        logging.info("MQTT (%s) %s connected return %d", self.service_name, self.host, rc)

    def on_disconnect(self, client, rc):
        logging.info("MQTT (%s) %s disconnect return %d", self.service_name, self.host, rc)

    def on_message(self, client, msg):
        logging.info("MQTT (%s) %s message recevied topic %s", self.service_name, self.host, msg.topic)

    def publish(self, topic, payload, qos=1):
        topic = "v1/{0}/{1}".format(self.service_name, topic)
        return self.mqttc.publish(topic=topic, payload=payload, qos=qos)

    def subscribe(self, topic):
        topic = "v1/{0}/{1}".format(self.service_name, topic)
        return self.mqttc.subscribe(topic)
