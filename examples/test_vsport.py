import logging
import time
from vspax.tcp_client_h import TcpClientHander


if __name__ == "__main__":
    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=formatter)

    # peer_handler = TcpClientHander(port, "172.30.1.143", 2003, "")
    port = TcpClientHander('COM9', "bj.proxy.thingsroot.com", 23112, "")
    port.start()

    while True:
        time.sleep(10)