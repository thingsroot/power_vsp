import logging
from vspc.mqtt_pub import MQTTStreamPub
from vspc.manager import VSPCManager
from vspc.service import VSPC_Service
from vspc.admin import vspc_admin
import time

def init():
    vspc_stream_pub = MQTTStreamPub()
    logging.info("Staring mqtt stream publisher..")
    vspc_stream_pub.start()
    time.sleep(1)

    vspc_manager = VSPCManager(vspc_stream_pub)
    logging.info("Staring vspc manager..")
    vspc_manager.start()

    vspc_service = VSPC_Service(vspc_manager)
    logging.info("Staring vspc service..")
    vspc_service.start()

    return vspc_admin, vspc_service