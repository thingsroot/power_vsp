#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
from common.mqtt_pub import MQTTStreamPub
from common.manager import UPDATEManager
from common.service import UPDATE_Service
from common.admin import update_admin
import time


def init():
    stream_pub = MQTTStreamPub()
    logging.info("Staring mqtt update publisher..")
    stream_pub.start()
    time.sleep(2)

    manager = UPDATEManager(stream_pub)
    logging.info("Staring update manager..")
    manager.start()

    service = UPDATE_Service(manager)
    logging.info("Staring update service..")
    service.start()

    return update_admin, service