import logging
import os
from services_runner import Services_Runner
from cloud_services.vspc import VSPC_Service

if __name__ == '__main__':
    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.INFO, format=formatter)
    bin_x86_path = os.path.dirname(os.path.realpath(__file__)) + "/bin_x86/"
    runner = Services_Runner(bin_x86_path, bin_x86_path + "mosquitto.exe")
    runner.start()

    vspc_service = VSPC_Service()
    vspc_service.start()

    runner.join(10000)
