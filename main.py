import logging
import os
import sys
import importlib
from hbmqtt_broker import MQTTBroker
from admin import start_admin
from helper import _dict

serivces = [
    'vspc',
    'vnet'
]

blueprints = []
context = _dict({})

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

    broker = MQTTBroker()
    logging.info("Staring hbmqtt broker..")
    broker.start()

    for m in serivces:
        service_module = importlib.import_module('{0}.app'.format(m))
        blueprint, service = service_module.init()
        blueprints.append(blueprint)
        service_name = "{0}_service".format(m)
        context[service_name] = service

    logging.info("Staring Admin!!")
    start_admin(blueprints, context)
    logging.info("CLOSING!!")
