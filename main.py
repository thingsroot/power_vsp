import logging
import os
import sys
# from services_runner import Services_Runner
from hbmqtt_broker import MQTTBroker
from mqtt_stream_pub import MQTTStreamPub
from vspc.manager import VSPCManager
from cloud_services.vspc_service import VSPC_Service
from admin import start_admin
from vspc_conf import broker_config
import encodings.idna

if __name__ == '__main__':
    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.INFO, format=formatter)
    # bin_x86_path = os.path.dirname(os.path.realpath(__file__)) + "/bin_x86/"
    # runner = Services_Runner(bin_x86_path, bin_x86_path + "mosquitto.exe")
    # logging.info("Staring service runner..")
    # runner.start()
    logging.info("当前工作路径：" + str(os.getcwd()))
    if sys.argv[0] != os.path.split(os.path.realpath(__file__))[1]:
        os.chdir(os.path.split(sys.argv[0])[0])

    broker = MQTTBroker(broker_config)
    logging.info("Staring hbmqtt broker..")
    broker.start()

    vspc_stream_pub = MQTTStreamPub()
    logging.info("Staring mqtt stream publisher..")
    vspc_stream_pub.start()

    vspc_manager = VSPCManager(vspc_stream_pub)
    logging.info("Staring vspc manager..")
    vspc_manager.start()

    vspc_service = VSPC_Service(vspc_manager)
    logging.info("Staring vspc service..")
    vspc_service.start()

    logging.info("Staring Admin!!")
    start_admin(vspc_manager, vspc_service)
    logging.info("CLOSING!!")
