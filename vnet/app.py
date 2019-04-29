#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
from vnet.mqtt_pub import MQTTStreamPub
from vnet.manager import VNETManager
from vnet.service import VNET_Service
from vnet.admin import vnet_admin
import time


def init():
    stream_pub = MQTTStreamPub()
    logging.info("Staring mqtt vnet publisher..")
    stream_pub.start()
    time.sleep(1)

    manager = VNETManager(stream_pub)
    logging.info("Staring vnet manager..")
    manager.start()

    service = VNET_Service(manager)
    logging.info("Staring vnet service..")
    service.start()

    return vnet_admin, service