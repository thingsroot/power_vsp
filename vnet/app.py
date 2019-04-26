#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
from vnet.mqtt_pub import MQTTStreamPub
from vnet.manager import VNETManager
from vnet.service import VNET_Service
from vnet.admin import vnet_admin


def init():
    stream_pub = MQTTStreamPub()
    logging.info("Staring mqtt stream publisher..")
    stream_pub.start()

    manager = VNETManager(stream_pub)
    logging.info("Staring vspc manager..")
    manager.start()

    service = VNET_Service(manager)
    logging.info("Staring vspc service..")
    service.start()

    return vnet_admin, service