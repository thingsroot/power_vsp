import logging
from vspax.mqtt_pub import MQTTStreamPub
from vspax.manager import VSPAXManager
from vspax.service import VSPAX_Service
from vspax.admin import vspax_admin
import time

def init():
    vspax_stream_pub = MQTTStreamPub()
    logging.info("Staring mqtt stream publisher..")
    vspax_stream_pub.start()
    time.sleep(1)

    vspax_manager = VSPAXManager(vspax_stream_pub)
    logging.info("Staring vspax manager..")
    vspax_manager.start()

    vspax_service = VSPAX_Service(vspax_manager)
    logging.info("Staring vspax service..")
    vspax_service.start()

    return vspax_admin, vspax_service